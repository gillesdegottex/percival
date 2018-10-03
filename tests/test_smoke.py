# http://pymbook.readthedocs.io/en/latest/testing.html

import percivaltts

import unittest

import numpy as np
percivaltts.numpy_force_random_seed()

cptest = 'tests/slt_arctic_merlin_test/'
lab_size = 425
spec_size = 65
nm_size = 17


class TestSmoke(unittest.TestCase):
    def test_percivaltts(self):
        import percivaltts

        cfg = percivaltts.configuration()

        text_file = open(cptest+'/info.py', "w")
        text_file.write("fs = 16000\n")
        text_file.write("shift = 0.005\n")
        text_file.close()
        cfg.mergefiles([cptest+'/info.py'])
        cfg.mergefiles(cptest+'/info.py')

        percivaltts.print_log('print_log')

        percivaltts.print_tty('print_tty', end='\n')

        print(percivaltts.datetime2str(sec=1519426184))

        print(percivaltts.time2str(sec=1519426184))

        percivaltts.makedirs('/dev/null')

        self.assertTrue(percivaltts.is_int('74324'))
        self.assertFalse(percivaltts.is_int('743.24'))

        rng = np.random.RandomState(123)
        percivaltts.weights_normal_ortho(32, 64, 1.0, rng, dtype=np.float32)

        memres = percivaltts.proc_memresident()
        print(memres)
        self.assertNotEqual(memres, -1)

        percivaltts.print_sysinfo()

        # percivaltts.print_sysinfo_theano() TODO
        # percivaltts.log_plot_costs(costs_tra, costs_val, worst_val, fname, epochs_modelssaved, costs_critic=[]) TODO
        # percivaltts.log_plot_costs(costs, worst_val, fname, epochs_modelssaved) TODO
        # percivaltts.log_plot_samples() TODO

    def test_data(self):
        import percivaltts.data

        fids = percivaltts.readids(cptest+'file_id_list.scp')

        path, shape = percivaltts.data.getpathandshape('dummy.fwlspec')
        self.assertTrue(path=='dummy.fwlspec')
        self.assertTrue(shape==None)
        path, shape = percivaltts.data.getpathandshape('dummy.fwlspec:(-1,129)')
        self.assertTrue(path=='dummy.fwlspec')
        self.assertTrue(shape==(-1,129))
        path, shape = percivaltts.data.getpathandshape('dummy.fwlspec:(-1,129)', (-1,12))
        self.assertTrue(path=='dummy.fwlspec')
        self.assertTrue(shape==(-1,12))
        path, shape = percivaltts.data.getpathandshape('dummy.fwlspec', (-1,12))
        self.assertTrue(path=='dummy.fwlspec')
        self.assertTrue(shape==(-1,12))
        dim = percivaltts.data.getlastdim('dummy.fwlspec')
        self.assertTrue(dim==1)
        dim = percivaltts.data.getlastdim('dummy.fwlspec:(-1,129)')
        self.assertTrue(dim==129)

        indir = cptest+'binary_label_'+str(lab_size)+'_norm_minmaxm11/*.lab:(-1,'+str(lab_size)+')'
        Xs = percivaltts.data.load(indir, fids, shape=None, frameshift=0.005, verbose=1, label='Xs: ')
        self.assertTrue(len(Xs)==10)
        print(Xs[0].shape)
        self.assertTrue(Xs[0].shape==(667, lab_size))

        print(percivaltts.data.gettotallen(Xs))
        self.assertTrue(percivaltts.data.gettotallen(Xs)==5694)

        outdir = cptest+'wav_cmp_lf0_fwlspec65_fwnm17_bndnmnoscale/*.cmp:(-1,83)'
        Ys = percivaltts.data.load(outdir, fids, shape=None, frameshift=0.005, verbose=1, label='Ys: ')
        print('len(Ys)='+str(len(Ys)))
        self.assertTrue(len(Ys)==10)
        print('Ys[0].shape'+str(Ys[0].shape))
        self.assertTrue(Ys[0].shape==(666, 83))

        wdir = cptest+'wav_fwlspec65_weights/*.w:(-1,1)'
        Ws = percivaltts.data.load(wdir, fids, shape=None, frameshift=0.005, verbose=1, label='Ws: ')
        self.assertTrue(len(Ws)==10)

        Xs, Ys, Ws = percivaltts.data.croplen([Xs, Ys, Ws])

        [Xs, Ys], Ws = percivaltts.data.croplen_weight([Xs, Ys], Ws, thresh=0.5)

        Xs_w_stop =percivaltts. data.addstop(Xs)

        X_train, Y_train, W_train = percivaltts.data.load_inoutset(indir, outdir, wdir, fids, length=None, lengthmax=100, maskpadtype='randshift', inouttimesync=False)
        X_train, Y_train, W_train = percivaltts.data.load_inoutset(indir, outdir, wdir, fids, length=None, lengthmax=100, maskpadtype='randshift')
        X_train, Y_train, W_train = percivaltts.data.load_inoutset(indir, outdir, wdir, fids, length=None, lengthmax=100, maskpadtype='randshift', cropmode='begendbigger')
        X_train, Y_train, W_train = percivaltts.data.load_inoutset(indir, outdir, wdir, fids, length=None, lengthmax=100, maskpadtype='randshift', cropmode='all')

        worst_val = percivaltts.data.cost_0pred_rmse(Ys)
        print('worst_val={}'.format(worst_val))

        worst_val = percivaltts.data.cost_0pred_rmse(Ys[0])
        print('worst_val={}'.format(worst_val))

        def data_cost_model_mfn(Xs, Ys):
            return np.std(Ys) # TODO More usefull
        X_vals = percivaltts.data.load(indir, fids)
        Y_vals = percivaltts.data.load(outdir, fids)
        X_vals, Y_vals = percivaltts.data.croplen([X_vals, Y_vals])
        cost = percivaltts.data.cost_model_mfn(data_cost_model_mfn, [X_vals, Y_vals])
        print(cost)

        class SmokyModel:
            def predict(self, Xs):
                return np.zeros([1, Xs.shape[1], 83])
        mod = SmokyModel()
        cost = percivaltts.data.cost_model_prediction_rmse(mod, [Xs], Ys)
        print(cost)

        std = percivaltts.data.prediction_mstd(mod, [Xs])
        print(std)

        rms = percivaltts.data.prediction_rms(mod, [Xs])
        print(rms)

    def test_compose(self):
        import percivaltts.data
        import percivaltts.compose

        fids = percivaltts.readids(cptest+'/file_id_list.scp')

        wav_dir = 'wav'
        f0_path = cptest+wav_dir+'_lf0/*.lf0'
        spec_path = cptest+wav_dir+'_fwlspec'+str(spec_size)+'/*.fwlspec'
        nm_path = cptest+wav_dir+'_fwnm'+str(nm_size)+'/*.fwnm'

        percivaltts.compose.compose([cptest+'binary_label_'+str(lab_size)+'/*.lab:(-1,'+str(lab_size)+')'], fids, 'tests/test_made__smoke_compose_compose_lab0/*.lab', id_valid_start=8, normfn=None, wins=[], dropzerovardims=False)

        percivaltts.compose.compose([cptest+'binary_label_'+str(lab_size)+'/*.lab:(-1,'+str(lab_size)+')'], fids, 'tests/test_made__smoke_compose_compose_lab1/*.lab', id_valid_start=8, normfn=percivaltts.compose.normalise_minmax, wins=[], dropzerovardims=False)

        path2, shape2 = percivaltts.data.getpathandshape('tests/test_made__smoke_compose_compose_lab1/*.lab:(mean.dat,'+str(lab_size)+')')

        percivaltts.compose.compose([cptest+'binary_label_'+str(lab_size)+'/*.lab:(-1,'+str(lab_size)+')'], fids, 'tests/test_made__smoke_compose_compose_lab2/*.lab', id_valid_start=8, normfn=percivaltts.compose.normalise_minmax, wins=[], dropzerovardims=True)

        percivaltts.compose.compose([f0_path, spec_path+':(-1,'+str(spec_size)+')', nm_path+':(-1,'+str(nm_size)+')'], fids, 'tests/test_made__smoke_compose_compose2_cmp1/*.cmp', id_valid_start=8, normfn=percivaltts.compose.normalise_minmax, wins=[])

        percivaltts.compose.compose([f0_path, spec_path+':(-1,'+str(spec_size)+')', nm_path+':(-1,'+str(nm_size)+')'], fids, 'tests/test_made__smoke_compose_compose2_cmp2/*.cmp', id_valid_start=8, normfn=percivaltts.compose.normalise_meanstd, wins=[])

        percivaltts.compose.compose([f0_path, spec_path+':(-1,'+str(spec_size)+')', nm_path+':(-1,'+str(nm_size)+')'], fids, 'tests/test_made__smoke_compose_compose2_cmp4/*.cmp', id_valid_start=8, normfn=percivaltts.compose.normalise_meanstd_nmnoscale, wins=[])

        percivaltts.compose.compose([f0_path, spec_path+':(-1,'+str(spec_size)+')', nm_path+':(-1,'+str(nm_size)+')'], fids, 'tests/test_made__smoke_compose_compose2_cmp_deltas/*.cmp', id_valid_start=8, normfn=percivaltts.compose.normalise_meanstd_nmnoscale, wins=[[-0.5, 0.0, 0.5], [1.0, -2.0, 1.0]])

        # WORLD vocoder features
        percivaltts.compose.compose([cptest+wav_dir+'_world_lf0/*.lf0', cptest+wav_dir+'_world_fwlspec/*.fwlspec:(-1,'+str(spec_size)+')', cptest+wav_dir+'_world_fwdbaper/*.fwdbaper:(-1,'+str(nm_size)+')', cptest+wav_dir+'_world_vuv/*.vuv'], fids, 'tests/test_made__smoke_compose_compose2_cmp_WORLD/*.cmp', id_valid_start=8, normfn=percivaltts.compose.normalise_meanstd, wins=[])
        percivaltts.compose.compose([cptest+wav_dir+'_world_lf0/*.lf0', cptest+wav_dir+'_world_fwlspec/*.fwlspec:(-1,'+str(spec_size)+')', cptest+wav_dir+'_world_fwdbaper/*.fwdbaper:(-1,'+str(nm_size)+')', cptest+wav_dir+'_world_vuv/*.vuv'], fids, 'tests/test_made__smoke_compose_compose2_cmp_WORLD_mlpg/*.cmp', id_valid_start=8, normfn=percivaltts.compose.normalise_meanstd, wins=[[-0.5, 0.0, 0.5], [1.0, -2.0, 1.0]])

        percivaltts.compose.create_weights_spec(spec_path+':(-1,'+str(spec_size)+')', fids, 'tests/test_made__smoke_compose_compose2_w1/*.w', spec_type='fwlspec', thresh=-32)


if __name__ == '__main__':
    unittest.main()
