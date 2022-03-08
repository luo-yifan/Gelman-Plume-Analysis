import datetime
import math
import os

import numpy as np
import pandas
import pandas as pd

from sklearn.metrics import mean_squared_error


def calc_rmse(cache_dir_simple, cache_dir_rm5, DATE_COL, Y_COL, output_csv_name):
    sum_data = []

    def search_nearest_data(data, search_date):
        def error_datetime_str(str_a, str_b):
            str_a = str_a[:10]
            str_b = str_b[:10]
            a_obj = datetime.datetime.strptime(str_a, '%Y-%m-%d')
            b_obj = datetime.datetime.strptime(str_b, '%Y-%m-%d')
            return abs(a_obj - b_obj)

        def find_next_year_data(str_a, str_b):
            str_a = str_a[:10]
            str_b = str_b[:10]
            a_obj = datetime.datetime.strptime(str_a, '%Y-%m-%d')
            b_obj = datetime.datetime.strptime(str_b, '%Y-%m-%d')
            if a_obj.year + 1 == b_obj.year:
                return True
            return False

        min_period = error_datetime_str(data.iloc[0][DATE_COL], search_date)
        return_value = data.iloc[0]['y']
        return_date = data.iloc[0][DATE_COL]
        within_a_year = []
        for _, row_ in data.iterrows():
            if find_next_year_data(search_date, row_[DATE_COL]):
                within_a_year.append(row_['y'])

        if len(within_a_year) > 0:
            y_loss = []
            for i_ in within_a_year:
                y_loss.append(i_)
            return_value = np.asarray(y_loss).mean()
            return_date = datetime.datetime.strptime(search_date[:10], '%Y-%m-%d').year + 1

        else:
            for _, row_ in data.iterrows():
                t = error_datetime_str(row_[DATE_COL], search_date)
                if t < min_period:
                    min_period = t
                    return_value = row_['y']
                    return_date = row_[DATE_COL]
        return return_date, return_value

    name_list = [name for name in os.listdir(cache_dir_rm5)]

    count = 0.0
    well_count = 0.0
    for i in name_list:
        predict_data = pd.read_csv(cache_dir_rm5 + i + '/predict.csv')
        ori_data = pd.read_csv(cache_dir_simple + i + '/data.csv')
        sum_per_well = 0.0
        count_per_well = 0.0
        y_true = []
        y_pred = []
        df_row = [i]
        for index, row in predict_data.iterrows():
            cur_date = row['Date']
            cur_value = row[Y_COL]
            if pd.isna(cur_value):
                continue
            nearest_date, nearest_value = search_nearest_data(ori_data, cur_date)
            error_square = (cur_value - nearest_value) ** 2
            if abs(cur_value - nearest_value) > 1e10:
                df_row.append(np.NAN)
                df_row.append(np.NAN)
                df_row.append(np.NAN)
                df_row.append(np.NAN)
                continue
            y_true.append(nearest_value)
            y_pred.append(cur_value)

            df_row.append(cur_date)
            df_row.append(cur_value)
            df_row.append(nearest_date)
            df_row.append(nearest_value)

            sum_per_well += error_square
            count_per_well += 1.0
            print(i, cur_date, cur_value, 'error:', error_square, '|', nearest_date, nearest_value)
            count += 1.0
        sum_data.append(df_row)

        if count_per_well == 0:
            continue
        well_count += 1
    df = pd.DataFrame(sum_data, columns=['WellName',
                                         'y_pred_1_date', 'y_pred_1_value',
                                         'y_ture_1_date', 'y_true_1_value',
                                         'y_pred_2_date', 'y_pred_2_value',
                                         'y_ture_2_date', 'y_true_2_value',
                                         'y_pred_3_date', 'y_pred_3_value',
                                         'y_ture_3_date', 'y_true_3_value',
                                         'y_pred_4_date', 'y_pred_4_value',
                                         'y_ture_4_date', 'y_true_4_value',
                                         'y_pred_5_date', 'y_pred_5_value',
                                         'y_ture_5_date', 'y_true_5_value',
                                         ])
    df.to_csv(output_csv_name + '.csv')
    return df


def calc(input_csv, output_csv):
    df = pd.read_csv(input_csv+'.csv')
    rmse_list = []
    for index, row in df.iterrows():
        y_true = [row['y_true_1_value'], row['y_true_2_value'], row['y_true_3_value'], row['y_true_4_value'],
                  row['y_true_5_value']]
        y_pred = [row['y_pred_1_value'], row['y_pred_2_value'], row['y_pred_3_value'], row['y_pred_4_value'],
                  row['y_pred_5_value']]
        print(y_true)
        print(y_pred)
        try:
            rmse = mean_squared_error(y_true, y_pred)
            rmse_list.append(rmse)
        except:
            rmse_list.append(np.NAN)
            continue
    df['rmse'] = rmse_list
    df.to_csv(output_csv+'.csv')

def combine(ori_df1, rec_df2,output):
    data = []
    for index, row in ori_df1.iterrows():
        rname = row['WellName']
        for i2, r2 in rec_df2.iterrows():
            if r2['WellName'].split('@')[0] == rname.replace(' ', '-'):
                row['rec_y_pred_1_date'] = r2['y_pred_1_date']
                row['rec_y_pred_1_value'] = r2['y_pred_1_value']
                row['rec_y_pred_2_date'] = r2['y_pred_2_date']
                row['rec_y_pred_2_value'] = r2['y_pred_2_value']
                row['rec_y_pred_3_date'] = r2['y_pred_3_date']
                row['rec_y_pred_3_value'] = r2['y_pred_3_value']
                row['rec_y_pred_4_date'] = r2['y_pred_4_date']
                row['rec_y_pred_4_value'] = r2['y_pred_4_value']
                row['rec_y_pred_5_date'] = r2['y_pred_5_date']
                row['rec_y_pred_5_value'] = r2['y_pred_5_value']
                row['rec_rmse'] = r2['rmse']
                data.append(row)
                break
    df = pd.concat(data, axis=1).T
    df.to_csv(output+'.csv')






if __name__ == "__main__":
    # ori_df = calc_rmse('../result/ori/simple/cache/',
    #                    '../result/ori/rm5/cache/',
    #                    'Date',
    #                    'y','ori')
    # rec_df = calc_rmse('../result/well_rec/simple/cache/',
    #                    '../result/well_rec/rm5/cache/',
    #                    'ds',
    #                    'Concentration','rec')
    # calc('ori','ori_rmse')
    # calc('rec','rec_rmse')
    df1 = pd.read_csv('ori_rmse.csv')
    df2 = pd.read_csv('rec_rmse.csv')
    combine(df1,df2,'combined_rmse')
