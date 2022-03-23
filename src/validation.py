import statistics
import pymannkendall as mk


def validation(ori, pred):
    ori_mk = mk.original_test(ori)
    pred_mk = mk.original_test(pred)
    if ori_mk.h == True and ori_mk.p < 0.05:
        if pred_mk.h == True and pred_mk.p < 0.005:
            if ori_mk.trend != pred_mk.trend and statistics.mean(ori) > 4 and statistics.mean(pred) > 4:
                return False
        if ori_mk.trend == 'decreasing':
            if max(ori) * 1.5 < max(pred):
                return False
        elif ori_mk.trend == 'increasing':
            if statistics.mean(ori) * 3.0 < statistics.mean(pred):
                return False
    else:
        if statistics.mean(ori) * 10.0 < statistics.mean(pred):
            return False
    return True
