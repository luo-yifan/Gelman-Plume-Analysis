import pathlib
import pandas as pd
from pathlib import Path


class Utils:
    def __init__(self):
        self.cache_dir = pathlib.Path('../history/cache/')
        self.module_dir = pathlib.Path('../result/mod/')

    def get_ori_predict(self, well_name):
        well_name_dir = self.cache_dir.joinpath(well_name)
        if not well_name_dir.exists(): return None
        ori = pd.read_csv(well_name_dir.joinpath('data.csv'), parse_dates=['Date'], index_col=0, squeeze=True)
        predict = pd.read_csv(well_name_dir.joinpath('predict.csv'), parse_dates=['Date'], index_col=0, squeeze=True)
        return ori, predict

    def get_model_description(self, well_name):
        if not self.module_dir.exists(): return None
        model_str = self.module_dir.joinpath(well_name + '.txt').read_text()
        return model_str

    def get_model_name(self, model_str):
        str_list = model_str.split('\n')
        if len(str_list) >= 2:
            return str_list[1]
        else:
            return None
