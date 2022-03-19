import datetime
import multiprocessing
import os
import pathlib
from autots import AutoTS
from functools import partial
import pandas as pd


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


def predict_single_full(output_directory, m_list, remove_recent_years, grouped_by_name):
    name, group = grouped_by_name

    if len(group) < 20:
        print('skip ' + name, ':length is less than 20.')
        return
    if os.path.exists(output_directory + '/cache/' + name):
        print('skip ' + name, ':cache exists.')
        return

    group['Date'] = pd.to_datetime(group['ds'])
    # ori_group = group[:]
    # ori_group.set_index('Date', inplace=True)

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
        prediction = mod.predict()
        forecast = prediction.forecast
    except:
        # TODO: catch well names
        print('predict or mod fit error:', name)
        return

    ft = open(output_directory + "/mod/" + name + '.txt', "w")
    ft.write(str(mod))
    ft.close()

    # fig, ax = plt.subplots()
    # ax.scatter(ori_group.y.index, ori_group.y, label='a')
    # ax.scatter(forecast.index, forecast, label='b')
    # ax.set_title(name)
    # plt.savefig(output_directory + "/fig/" + name + '.png')

    cache_dir = pathlib.Path(output_directory + '/cache/' + name)
    cache_dir.mkdir(parents=True, exist_ok=True)
    group.y.to_csv(cache_dir.joinpath('data.csv'))
    # TODO: "raw_input.csv"
    forecast.index.name = "Date"
    forecast.squeeze().to_csv(cache_dir.joinpath('predict.csv'))
    # TODO: "pred_output.csv"


def run(output_directory, m_list):
    create_dir(output_directory)
    well_data = pd.read_excel('../data/Gelman_2020_DATA_Rockworks6-2020.xlsx',
                              sheet_name='TmInterval')
    well_data.loc[:, 'y'] = pd.to_numeric(well_data['Value'])
    well_data.loc[:, 'ds'] = pd.to_datetime(well_data['SampleDate'])
    grouped = well_data.groupby('Bore')
    print(grouped)
    pool = multiprocessing.Pool(processes=4)
    predict = partial(predict_single_full, output_directory, m_list, False)
    pool.map(predict, grouped)


def run_from_ori(output_directory, m_list, n_jobs, remove_recent_years=False):
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
        # ori_group = group[:]
        # ori_group.set_index('Date', inplace=True)

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
                     verbose=-4,
                     n_jobs=n_jobs
                     )

        try:
            mod = mod.fit(group, date_col='ds', value_col='y', id_col=None)
            prediction = mod.predict()
            forecast = prediction.forecast
        except:
            # TODO: catch well names
            continue

        create_dir(output_directory + "mod/")
        create_dir(output_directory + "cache/")
        # create_dir(output_directory + "fig/")

        ft = open(output_directory + "/mod/" + name + '.txt', "w")
        ft.write(str(mod))
        ft.close()

        # fig, ax = plt.subplots()
        # ax.scatter(ori_group.y.index, ori_group.y, label='a')
        # ax.scatter(forecast.index, forecast, label='b')
        # ax.set_title(name)
        # plt.savefig(output_directory + "/fig/" + name + '.png')

        cache_dir = pathlib.Path(output_directory + '/cache/' + name)
        cache_dir.mkdir(parents=True, exist_ok=True)
        group.y.to_csv(cache_dir.joinpath('data.csv'))
        # TODO: "raw_input.csv"
        forecast.index.name = "Date"
        forecast.squeeze().to_csv(cache_dir.joinpath('predict.csv'))
        # TODO: "pred_output.csv"
        all_well_data.append((name, group.y, forecast, mod))
        count += 1


def run_from_rec(output_directory, m_list, n_jobs, name_dict, remove_recent_years=False):
    create_dir(output_directory)
    name_list = [name for name in os.listdir("../data/Well_Rec_txt/")]
    count = 0
    len_name_list = len(name_list)
    for i in name_list:
        count += 1
        name = i.split('.')[1]
        if i.split('.')[2] == 'S2020':
            name = name_dict[name]
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

            mod = AutoTS(forecast_length=5,
                         frequency='Y',
                         no_negatives=True,
                         min_allowed_train_percent=0.2,
                         model_list=m_list,
                         n_jobs=n_jobs,
                         verbose=-4)
            try:
                mod = mod.fit(well_data, date_col='Date', value_col='Concentration', id_col=None)
                prediction = mod.predict()
                forecast = prediction.forecast
            except:
                # TODO: catch well names
                continue

            create_dir(output_directory + "mod/")
            create_dir(output_directory + "cache/")
            create_dir(output_directory + "fig/")

            ft = open(output_directory + "mod/" + name + '.txt', "w")
            ft.write(str(mod))
            ft.close()

            # fig, ax = plt.subplots()
            # ax.scatter(well_data.y.index, well_data.y, label='a')
            # ax.scatter(forecast.index, forecast, label='b')
            # ax.set_title(name)
            # plt.savefig(output_directory + '/fig/' + name + '.png')

            cache_dir = pathlib.Path(output_directory + '/cache/' + name)
            cache_dir.mkdir(parents=True, exist_ok=True)

            well_data.y.to_csv(cache_dir.joinpath('data.csv'))
            forecast.index.name = "Date"
            forecast.squeeze().to_csv(cache_dir.joinpath('predict.csv'))

            print("[predict success]", name, count, '/', len_name_list)


def run_from_pixel_rec(output_directory, m_list, n_jobs):
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

        mod = AutoTS(forecast_length=5,
                     frequency='Y',
                     no_negatives=True,
                     min_allowed_train_percent=0.2,
                     model_list=m_list,
                     n_jobs=n_jobs,
                     verbose=-4)

        try:
            mod = mod.fit(pixel_data, date_col='Date', value_col='Conc', id_col=None)
            prediction = mod.predict()
            forecast = prediction.forecast
        except:
            # TODO: catch well names
            continue

        create_dir(output_directory + "mod/")
        create_dir(output_directory + "res/")
        create_dir(output_directory + "fig/")

        ft = open(output_directory + "mod/" + name + '.txt', "w")
        ft.write(str(mod))
        ft.close()

        # fig, ax = plt.subplots()
        # ax.scatter(pixel_data.y.index, pixel_data.y, label='a')
        # ax.scatter(forecast.index, forecast, label='b')
        # ax.set_title(name)
        # plt.savefig(output_directory + '/fig/' + name + '.png')

        ori_data = pd.read_csv('../data/pixel_rec/' + i).dropna()

        for row_datetime, row in forecast.iterrows():
            dt = pd.to_datetime(row_datetime)
            to_append = {'Year': dt.year, 'Month': dt.month, 'Conc': row['Conc']}
            ori_data = ori_data.append(to_append, ignore_index=True)
        ori_data = ori_data.astype({'Year': 'int32', 'Month': 'int32'})

        ori_data.to_csv(output_directory + '/res/' + name + '.txt')

        print("[predict success]", name, count, '/', len_name_list)


if __name__ == '__main__':

    # run_from_ori( '../result/ori/simple_parallel_test/', 'default', 32, False)

    # run_from_ori( '../result/ori/rm5_parallel_test/', 'default', 32, True)

    # run_from_rec('../result/well_rec/simple_parallel_test/', 'default',32,generate_name_dict(), False)

    # run_from_rec('../result/well_rec/rm5_parallel_test/', 'default',32,generate_name_dict(), True)

    run_from_pixel_rec('../result/well_rec/simple_parallel_test/', 'default', 32)
