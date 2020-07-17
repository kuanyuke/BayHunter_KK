import os.path as op
import sys
sys.path.append("..")

from src.BayWatch import BayWatcher

configfile = op.join('.', 'baywatch.pkl')
pro = BayWatcher(configfile=configfile,save_plots=None)

#start baywatcher
pro.watch()
