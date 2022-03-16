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
                     n_jobs =16
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


if __name__ == '__main__':

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
    output_dir = '../result/ori/simple_parallel_test/'
    # run(output_dir, model_list)
    run_from_ori(output_dir, 'default', 32, False)
