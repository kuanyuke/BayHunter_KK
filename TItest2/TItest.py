
import os
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
import numpy as np
import os.path as op
import matplotlib
matplotlib.use('PDF')

import sys
sys.path.append("..")

from src import PlotFromStorage
from src import Targets
from src import utils
from src.mcmcOptimizer import MCMC_Optimizer
from src.Models import ModelMatrix, Model
from src.SynthObs import SynthObs

import logging



#
# console printout formatting
#
formatter = ' %(processName)-12s: %(levelname)-8s |  %(message)s'
logging.basicConfig(format=formatter, level=logging.INFO)
logger = logging.getLogger()


#
# ------------------------------------------------------------  obs SYNTH DATA
#
# Load priors and initparams from config.ini or simply create dictionaries.
initfile = 'config.ini'
priors, initparams = utils.load_params(initfile)

noise = [0.0, 0.012, 0.98, 0.005]
# Load observed data (synthetic test data)
xswsv, _yswsv = np.loadtxt('observed/st3_rdispph.dat').T
yswsv_err = SynthObs.compute_expnoise(_yswsv, corr=noise[0], sigma=noise[1])
yswsv = _yswsv + yswsv_err

xswsh, _yswsh = np.loadtxt('observed/st3_ldispph.dat').T
yswsh_err = SynthObs.compute_expnoise(_yswsh, corr=noise[0], sigma=noise[1])
yswsh = _yswsh + yswsh_err

## RF
xrf, _yrf = np.loadtxt('observed/st3_prf.dat').T
yrf_err = SynthObs.compute_gaussnoise(_yrf, corr=noise[2], sigma=noise[3])
yrf = _yrf + yrf_err

#
# -------------------------------------------  get reference model for BayWatch
#
# Create truemodel only if you wish to have reference values in plots
# and BayWatch. You ONLY need to assign the values in truemodel that you
# wish to have visible.
dep, vsv, vsh = np.loadtxt('observed/st3_mod.dat', usecols=[0, 2, 3], skiprows=1).T
pdep = np.concatenate((np.repeat(dep, 2)[1:], [150]))
pvsv = np.repeat(vsv, 2)
pvsh = np.repeat(vsh, 2)

truenoise = np.concatenate(([noise[0]], [np.std(yswsv_err)],   # target 1
                            [noise[2]], [np.std(yrf_err)],  # target 2	
                            [noise[0]], [np.std(yswsh_err)]))  # target 3

explike = SynthObs.compute_explike(yobss=[yswsv, yrf, yswsh], ymods=[_yswsv, _yrf,_yswsh],
                                   noise=truenoise, gauss=[False, True, False],
                                   rcond=initparams['rcond'])
truemodel = {'model': (pdep, pvsv, pvsh),
             'nlays': 3,
             'noise': truenoise,
             'explike': explike,
             }
            

print truenoise, explike

#  -----------------------------------------------------------  DEFINE TARGETS
#
# Only pass x and y observed data to the Targets object which is matching
# the data type. You can chose for SWD any combination of Rayleigh, Love, group
# and phase velocity. Default is the fundamendal mode, but this can be updated.
# For RF chose P or S. You can also use user defined targets or replace the
# forward modeling plugin wih your own module.
target1 = Targets.RayleighDispersionPhase(xswsv, yswsv, yerr=yswsv_err)
target2 = Targets.PReceiverFunction(xrf, yrf)
target2.moddata.plugin.set_modelparams(gauss=1., water=0.01, p=6.4)
target3 = Targets.LoveDispersionPhase(xswsh , yswsh, yerr=yswsh_err)
# Join the targets. targets must be a list instance with all targets
# you want to use for MCMC Bayesian inversion.
targets = Targets.JointTarget(targets=[target1, target2, target3])


#
#  ---------------------------------------------------  Quick parameter update
#
# "priors" and "initparams" from config.ini are python dictionaries. You could
# also simply define the dictionaries directly in the script, if you don't want
# to use a config.ini file. Or update the dictionaries as follows, e.g. if you
# have station specific values, etc.
# See docs/bayhunter.pdf for explanation of parameters

priors.update({'mohoest': (38, 4),  # optional, moho estimate (mean, std)
               'rfnoise_corr': 0.98,
               'swdnoise_corr': 0.
               # 'rfnoise_sigma': np.std(yrf_err),  # fixed to true value
               # 'swdnoise_sigma': np.std(ysw_err),  # fixed to true value
               })

initparams.update({'nchains': 5,
                   'iter_burnin': (2048 * 32),
                   'iter_main': (2048 * 16),
                   'propdist': (0.025, 0.025, 0.015, 0.005, 0.005,0.005),
                   })



#
#  -------------------------------------------------------  MCMC BAY INVERSION
#
# Save configfile for baywatch. refmodel must not be defined.
utils.save_baywatch_config(targets, path='.', priors=priors,
                           initparams=initparams, refmodel=truemodel)
optimizer = MCMC_Optimizer(targets, initparams=initparams, priors=priors,
                           random_seed=None)
# default for the number of threads is the amount of cpus == one chain per cpu.
# if baywatch is True, inversion data is continuously send out (dtsend)
# to be received by BayWatch (see below).
optimizer.mp_inversion(nthreads=6, baywatch=True, dtsend=1)


#
#
# #  ---------------------------------------------- Model resaving and plotting
path = initparams['savepath']
cfile = '%s_config.pkl' % initparams['station']
configfile = op.join(path, 'data', cfile)
obj = PlotFromStorage(configfile)
# The final distributions will be saved with save_final_distribution.
# Beforehand, outlier chains will be detected and excluded.
# Outlier chains are defined as chains with a likelihood deviation
# of dev * 100 % from the median posterior likelihood of the best chain.
obj.save_final_distribution(maxmodels=100000, dev=0.05)
# Save a selection of important plots
obj.save_plots(refmodel=truemodel)
obj.merge_pdfs()
