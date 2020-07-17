import numpy as np
import os.path as op
import logging
#from src import SynthObs
from BayHunter import Targets
logger = logging.getLogger()
class SynthObs1():
    """SynthObs is a class for computing synthetic 'observed' data.
    Used for testing purposes only. You can compute swd and rf data, and also
    synthetic noise using different correlation laws.
    You find also a method to compute the expected likelihood, for a given
    observed and modeled data set. This value can be feeded into BayWatch."""
    @staticmethod
    def return_swddata(h, vs, ra=None, vpvs=1.73, pars=dict(), x=None):
        """Return d ictionary of forward modeled data based on Surf96."""
	if x is None:
        	x = np.linspace(1, 40, 20)

        h = np.array(h)
        vs = np.array(vs)
        ra = np.array(ra)

        mode = pars.get('mode', 1)  # fundamental mode

        target1 = Targets.RayleighDispersionPhase(x=x, y=None)
        target1.moddata.plugin.set_modelparams(mode=mode)
        target2 = Targets.RayleighDispersionGroup(x=x, y=None)
        target2.moddata.plugin.set_modelparams(mode=mode)
        target3 = Targets.LoveDispersionPhase(x=x, y=None)
        target3.moddata.plugin.set_modelparams(mode=mode)
        target4 = Targets.LoveDispersionGroup(x=x, y=None)
        target4.moddata.plugin.set_modelparams(mode=mode)
        vp = vs * vpvs
        rho = vp * 0.32 + 0.77
        targets = [target1, target2, target3, target4]

        data = {}
        for i, target in enumerate(targets):
            xmod, ymod = target.moddata.plugin.run_model(
                h=h, vp=vp, vs=vs, ra=ra, rho=rho)
            data[target.ref] = np.array([xmod, ymod])
        logger.info('Compute SWD for %d periods, with model vp/vs %.2f.'
                    % (x.size, vpvs))
        return data
            
# idx = 1
# h = [34, 0]
# vs = [3.5, 4.4]

# idx = 2
# h = [5, 29, 0]
# vs = [3.4, 3.8, 4.5]

idx = 3
h = [5, 23, 8, 0]
vs = [2.7, 3.6, 3.8, 4.4]
ra = [5, 3, 2, 0] #%

vpvs = 1.73

path = 'observed'
datafile = op.join(path, 'st%d_%s.dat' % (idx, '%s'))

# surface waves
sw_x = np.linspace(1, 41, 21)
swdata = SynthObs1.return_swddata(h, vs, ra=ra, vpvs=vpvs, x=sw_x)
#print swdata
#synthObs.save_data(swdata, outfile=datafile)
