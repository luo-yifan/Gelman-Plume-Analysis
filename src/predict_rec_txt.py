import math
import pathlib
import os

import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
from autots import AutoTS
from sklearn.metrics import r2_score


def create_dir(filename):
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

def generate_name_dict():
    well_data = pd.read_excel('../data/Gelman_2020_DATA_Rockworks6-2020.xlsx',
                              sheet_name='TmInterval')
    grouped = well_data.groupby('Bore')
    dict = {}
    for name, _ in grouped:
        replaced_name = name.replace(' ', '-')
        dict[replaced_name] = name
    return dict

def run_rec(output_directory, m_list, remove_recent_years=False):
    create_dir(output_directory)
    name_list = [name for name in os.listdir("../data/Well_Rec_txt/")]
    count = 0
    len_name_list = len(name_list)
    for i in name_list:
        count += 1
        name = i.split('.')[1] + '@' + i.split('.')[2]
        if i.split('.')[2] == 'S2020':
            print(name)
            if os.path.exists(output_directory + '/cache/' + name):
                continue
            well_data = pd.read_csv('../data/Well_Rec_txt/' + i)
            well_data['Date'] = well_data.apply(lambda row: datetime.datetime(int(row.Year), int(row.Month), 1), axis=1)
            well_data['ds'] = pd.to_datetime(well_data['Date'])
            well_data['y'] = well_data['Concentration']
            if remove_recent_years:
                max_date = well_data['Date'].max() - datetime.timedelta(days=365 * 5)
                well_data = well_data[well_data['Date'] <= max_date]

            well_data.set_index('ds', inplace=True)
            fig, ax = plt.subplots()

            mod = AutoTS(forecast_length=5,
                         frequency='Y',
                         ensemble='simple',
                         no_negatives=True,
                         min_allowed_train_percent=0.2,
                         model_list=m_list,
                         verbose=-4)
            mod = mod.fit(well_data, date_col='Date', value_col='Concentration', id_col=None)
            prediction = mod.predict()
            forecast = prediction.forecast

            create_dir(output_directory + "mod/")
            create_dir(output_directory + "cache/")
            create_dir(output_directory + "fig/")

            ft = open(output_directory + "mod/" + name + '.txt', "w")
            ft.write(str(mod))
            ft.close()

            ax.scatter(well_data.y.index, well_data.y, label='a')
            ax.scatter(forecast.index, forecast, label='b')

            ax.set_title(name)
            plt.savefig(output_directory + '/fig/' + name + '.png')

            cache_dir = pathlib.Path(output_directory + '/cache/' + name)
            cache_dir.mkdir(parents=True, exist_ok=True)

            well_data.y.to_csv(cache_dir.joinpath('data.csv'))
            forecast.index.name = "Date"
            forecast.squeeze().to_csv(cache_dir.joinpath('predict.csv'))

            print("[predict success]", name, count, '/', len_name_list)


def run_rec_remove_invalid_date(output_directory,
                                m_list,
                                keep_date_consistent=True,
                                remove_recent_years=False):
    create_dir(output_directory)
    name_list = [name for name in os.listdir("../data/Well_Rec_txt/")]
    ori_dir = '../result/ori/rm5/cache/'
    ori_name_list = [name for name in os.listdir(ori_dir)]
    count = 0
    len_name_list = len(name_list)
    for i in name_list:
        count += 1
        name = i.split('.')[1] + '@' + i.split('.')[2]
        if i.split('.')[2] == 'S2020':
            print(name)
            if os.path.exists(output_directory + '/cache/' + name):
                continue
            well_data = pd.read_csv('../data/Well_Rec_txt/' + i)
            well_data['Date'] = well_data.apply(lambda row: datetime.datetime(int(row.Year), int(row.Month), 1), axis=1)
            well_data['ds'] = pd.to_datetime(well_data['Date'])
            well_data['y'] = well_data['Concentration']

            has_cut = False
            if keep_date_consistent:
                for ori_name in ori_name_list:
                    # print(ori_name.replace(' ', '-'))
                    stupid_name = i.split('.')[1]
                    if ori_name.replace(' ', '-') == stupid_name:
                        ori_data = pd.read_csv(ori_dir + ori_name + '/data.csv')
                        max_date = ori_data['Date'].max()
                        well_data = well_data[well_data['Date'] <= max_date]
                        has_cut = True
                        break
            if not has_cut:
                print("skip ", name, count, '/', len_name_list)
                continue

            if remove_recent_years:
                max_date = well_data['Date'].max() - datetime.timedelta(days=365 * 5)
                well_data = well_data[well_data['Date'] <= max_date]

            well_data.set_index('ds', inplace=True)
            fig, ax = plt.subplots()

            mod = AutoTS(forecast_length=5,
                         frequency='Y',
                         ensemble='simple',
                         no_negatives=True,
                         min_allowed_train_percent=0.2,
                         model_list=m_list,
                         verbose=-4)

            try:
                mod = mod.fit(well_data, date_col='Date', value_col='Concentration', id_col=None)
                prediction = mod.predict()
            except:
                # TODO: catch well names
                continue
            forecast = prediction.forecast

            create_dir(output_directory + "mod/")
            create_dir(output_directory + "cache/")
            create_dir(output_directory + "fig/")

            ft = open(output_directory + "mod/" + name + '.txt', "w")
            ft.write(str(mod))
            ft.close()

            ax.scatter(well_data.y.index, well_data.y, label='a')
            ax.scatter(forecast.index, forecast, label='b')

            ax.set_title(name)
            plt.savefig(output_directory + '/fig/' + name + '.png')

            cache_dir = pathlib.Path(output_directory + '/cache/' + name)
            cache_dir.mkdir(parents=True, exist_ok=True)

            well_data.y.to_csv(cache_dir.joinpath('data.csv'))
            forecast.index.name = "Date"
            forecast.squeeze().to_csv(cache_dir.joinpath('predict.csv'))

            print("[predict success]", name, count, '/', len_name_list)


def run_map_rec(output_directory, m_list):
    create_dir(output_directory)
    name_list = [name for name in os.listdir("../data/pixel_rec/")]
    count = 0
    len_name_list = len(name_list)
    for i in name_list:
        count += 1
        name = i.split('.')[0] + '.' + i.split('.')[1]
        print(name)
        if os.path.exists(output_directory + '/res/' + name + '.txt'):
            continue
        pixel_data = pd.read_csv('../data/pixel_rec/' + i)
        pixel_data = pixel_data.dropna()
        pixel_data['Date'] = pixel_data.apply(lambda row: datetime.datetime(int(row.Year), int(row.Month), 1), axis=1)
        pixel_data['ds'] = pd.to_datetime(pixel_data['Date'])
        pixel_data['y'] = pixel_data['Conc']

        pixel_data.set_index('ds', inplace=True)
        fig, ax = plt.subplots()

        mod = AutoTS(forecast_length=5,
                     frequency='Y',
                     ensemble='simple',
                     no_negatives=True,
                     min_allowed_train_percent=0.2,
                     model_list=m_list,
                     verbose=-4)
        mod = mod.fit(pixel_data, date_col='Date', value_col='Conc', id_col=None)
        prediction = mod.predict()
        forecast = prediction.forecast

        create_dir(output_directory + "mod/")
        create_dir(output_directory + "res/")
        create_dir(output_directory + "fig/")

        ft = open(output_directory + "mod/" + name + '.txt', "w")
        ft.write(str(mod))
        ft.close()

        ax.scatter(pixel_data.y.index, pixel_data.y, label='a')
        ax.scatter(forecast.index, forecast, label='b')

        ax.set_title(name)
        plt.savefig(output_directory + '/fig/' + name + '.png')

        ori_data = pd.read_csv('../data/pixel_rec/' + i).dropna()

        for row_datetime, row in forecast.iterrows():
            dt = pd.to_datetime(row_datetime)
            to_append = {'Year': dt.year, 'Month': dt.month, 'Conc': row['Conc']}
            ori_data = ori_data.append(to_append, ignore_index=True)
        ori_data = ori_data.astype({'Year': 'int32', 'Month': 'int32'})

        ori_data.to_csv(output_directory + '/res/' + name + '.txt')

        print("[predict success]", name, count, '/', len_name_list)


def run_from_ori(output_directory, m_list, remove_recent_years=False):
    create_dir(output_directory)
    well_data = pd.read_excel('../data/Gelman_2020_DATA_Rockworks6-2020.xlsx',
                              sheet_name='TmInterval')
    well_data.loc[:, 'y'] = pd.to_numeric(well_data['Value'])
    well_data.loc[:, 'ds'] = pd.to_datetime(well_data['SampleDate'])
    grouped = well_data.groupby('Bore')
    count = 0
    all_well_data = []
    for name, group in grouped:
        if len(group) < 20:
            print('skip ' + name, ':length is less than 20.')
            continue
        if os.path.exists(output_directory + '/cache/' + name):
            print('skip ' + name, ':cache exists.')
            continue
        group['Date'] = pd.to_datetime(group['ds'])
        ori_group = group[:]
        ori_group.set_index('Date', inplace=True)

        if remove_recent_years:
            max_date = group['Date'].max() - datetime.timedelta(days=365 * 5)
            group = group[group['Date'] <= max_date]

        group.set_index('Date', inplace=True)

        mod = AutoTS(forecast_length=5,
                     # TODO: Based on sample size
                     frequency='Y',
                     # TODO: ensemble method
                     ensemble='simple',
                     no_negatives=True,
                     model_list=m_list,
                     verbose=-4)

        try:
            mod = mod.fit(group, date_col='ds', value_col='y', id_col=None)
        except:
            # TODO: catch well names
            continue

        prediction = mod.predict()
        forecast = prediction.forecast

        create_dir(output_directory + "mod/")
        create_dir(output_directory + "cache/")
        create_dir(output_directory + "fig/")

        ft = open(output_directory + "/mod/" + name + '.txt', "w")
        ft.write(str(mod))
        ft.close()

        fig, ax = plt.subplots()
        ax.scatter(ori_group.y.index, ori_group.y, label='a')
        ax.scatter(forecast.index, forecast, label='b')
        ax.set_title(name)
        plt.savefig(output_directory + "/fig/" + name + '.png')

        cache_dir = pathlib.Path(output_directory + '/cache/' + name)
        cache_dir.mkdir(parents=True, exist_ok=True)
        group.y.to_csv(cache_dir.joinpath('data.csv'))
        # TODO: "raw_input.csv"
        forecast.index.name = "Date"
        forecast.squeeze().to_csv(cache_dir.joinpath('predict.csv'))
        # TODO: "pred_output.csv"
        all_well_data.append((name, group.y, forecast, mod))
        count += 1


def predict_cache_to_csv(cache_dir, output_dir, file_name):
    name_list = [name for name in os.listdir(cache_dir)]
    sum_data = []

    for i in name_list:
        print(i)
        well_data = pd.read_csv(cache_dir + i + '/predict.csv')
        well_data['WellName'] = i
        for index, row in well_data.iterrows():
            sum_data.append([row['WellName'], row['Date'], row['Concentration']])
    df = pd.DataFrame(sum_data, columns=['WellName', 'Date', 'Concentration'])
    # TODO: filename
    df.to_csv(output_dir + '/'+ file_name + '.csv')

def predict_cache_to_csv_ds_y(cache_dir, output_dir, file_name):
    name_list = [name for name in os.listdir(cache_dir)]
    sum_data = []

    for i in name_list:
        print(i)
        well_data = pd.read_csv(cache_dir + i + '/predict.csv')
        well_data['WellName'] = i
        for index, row in well_data.iterrows():
            sum_data.append([row['WellName'], row['Date'], row['y']])
    df = pd.DataFrame(sum_data, columns=['WellName', 'Date', 'Concentration'])
    # TODO: filename
    df.to_csv(output_dir + '/'+ file_name + '.csv')


def ori_data_to_csv(output_directory):
    name_list = [name for name in os.listdir("../data/Well_Rec_txt2/")]
    sum_data = []
    name_dict = generate_name_dict()
    for i in name_list:
        name = i.split('.')[1]
        if i.split('.')[2] == 'S2020':
            well_data = pd.read_csv('../data/Well_Rec_txt2/' + i)
            well_data['Date'] = well_data.apply(lambda row: datetime.datetime(int(row.Year), int(row.Month), 1), axis=1)
            if name not in name_dict.keys():
                name = name.split('_')[0]
            well_data['WellName'] = name_dict[name]
            for index, row in well_data.iterrows():
                sum_data.append([row['WellName'], row['Date'], row['Concentration']])
    df = pd.DataFrame(sum_data, columns=['WellName', 'Date', 'Concentration'])
    # TODO: filename
    df.to_csv(output_directory + '/all_rec_data.csv')


def pixel_data_to_csv(output_directory):
    name_list = [name for name in os.listdir("../data/pixel_rec/")]
    sum_data = []
    name_list.sort()
    for i in name_list:
        print(i)
        name = i.split('.')[1]
        row_str = name.split('-')[0]
        col_str = name.split('-')[1]
        row_num = int(row_str[1:])
        col_num = int(col_str[1:])

        well_data = pd.read_csv('../data/pixel_rec/' + i)
        well_data['Date'] = well_data.apply(lambda row: datetime.datetime(int(row.Year), int(row.Month), 1), axis=1)
        well_data['RowNum'] = row_num
        well_data['ColNum'] = col_num
        for index, row in well_data.iterrows():
            sum_data.append([row['RowNum'], row['ColNum'], row['Date'], row['Conc']])
    df = pd.DataFrame(sum_data, columns=['RowNum', 'ColNum', 'Date', 'Conc'])
    df.to_csv(output_directory + '/pixel_all.csv')


def calc_rmse(cache_dir_simple, cache_dir_rm5, DATE_COL, Y_COL):
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

    sum_error_square = 0.0
    count = 0.0
    well_count = 0.0
    r2 = []
    nrmse_list = []
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
        rmse_per_well = math.sqrt(sum_per_well / count_per_well)
        if np.asarray(y_true).mean() == 0:
            nrmse = 0
        else:
            nrmse = rmse_per_well / np.asarray(y_true).mean()
        # if nrmse > 5:
        #     continue
        r2_per_well = r2_score(y_true, y_pred)
        # if np.isnan(r2_per_well):
        #     continue
        # r2.append(r2_per_well)
        print(i, nrmse, rmse_per_well)
        sum_error_square += nrmse
        nrmse_list.append(nrmse)
        well_count += 1
    xxx = nrmse_list.sort(reverse=True)
    print(nrmse_list)
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
    df.to_csv('recent_five_years_rec_txt.csv')
    return sum_error_square / well_count


if __name__ == "__main__":
    # TODO: categorize
    model_list = [
        'LastValueNaive',
        'RollingRegression',
        'UnobservedComponents',
        'ZeroesNaive',
        'AverageValueNaive',
        'DatepartRegression',
        'GLS',
        'GLM',
        'ETS',
    ]
    # ori_data_to_csv(output_dir)

    # output_dir_ori = '../result/well_rec/rm_by_ori/'
    # output_dir = '../result/well_rec/simple/'
    # remove_recent_years_output_dir = '../result/well_rec/rm5/'
    # run_rec_remove_invalid_date(output_dir_ori, model_list)
    # dir = '../result/well_rec/rm5/cache/'

    # output_dir_ori = '../result/ori/rm5/'
    # run_from_ori(output_dir_ori, model_list, True)
    # predict_cache_to_csv(output_dir_ori + '/cache/', output_dir_ori)

    # dir = '../result/well_rec/simple/cache/'
    # predict_cache_to_csv(dir, output_dir)

    # print(calc_rmse('../result/ori/simple/cache/', '../result/ori/rm5/cache/', 'Date', 'y'))
    # print(calc_rmse('../result/well_rec/simple/cache/', '../result/well_rec/rm5/cache/', 'ds', 'Concentration'))

    # pixel_data_to_csv('../result/pixel_rec/')

    # output_dir_ori = '../result/pixel_rec/'
    # run_map_rec(output_dir_ori, model_list)

    predict_cache_to_csv('../result/well_rec/simple_parallel_test/cache/',
                         '../result/well_rec/simple_parallel_test/',
                         'all_predict_data_rec')
    # predict_cache_to_csv('../result/well_rec/rm5_parallel_test/cache/',
    #                      '../result/well_rec/rm5_parallel_test/',
    #                      'all_predict_data_rec_rm5')
    #
    # predict_cache_to_csv_ds_y('../result/ori/rm5_parallel_test/cache/',
    #                      '../result/ori/rm5_parallel_test/',
    #                      'rm5_predict_data')
    #
    # predict_cache_to_csv_ds_y('../result/ori/simple_parallel_test/cache/',
    #                      '../result/ori/simple_parallel_test/',
    #                      'all_predict_data_ori')

    # ori_data_to_csv('../data/')
