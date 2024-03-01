#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author: Tao Ran

import math
import xlrd
import xlwt
import openpyxl
from openpyxl import Workbook

class ParkingCharge:
    def __init__(self):
        self.file_path = 'your_file_path'
        self.free_spots = 83
        self.car_info = {}  # 新增一个字典来存储车辆的信息

    """
    读取excel中的内容
    """
    def read_excel(self):
        # 根据路径读取excel
        workbook = xlrd.open_workbook(self.file_path)
        # 根据sheet名称读取
        table = workbook.sheet_by_name('Sheet1')
        # 该sheet的行数，列数
        nrows = table.nrows
        ncols = table.ncols

        # 停车场的进出记录列表
        in_and_out_parking_list = []

        # 遍历文件的行列
        # 从第二行开始读
        for row in range(1, nrows):
            for col in range(ncols):
                # 记录的车进或出的信息字典
                car_time_info = dict()
                # 如果是第二列，记录进场信息
                if col == 1:
                    # 此时car_time_info如  {'英A0NF70': [datetime.datetime(2023, 6, 1, 6, 18, 35), 'entry']}
                    car_time_info[table.cell_value(row, col - 1)+"_"+str(xlrd.xldate_as_datetime(table.cell_value(row, col), 0))+"_"+str(xlrd.xldate_as_datetime(table.cell_value(row, col+1), 0))] = [xlrd.xldate_as_datetime(table.cell_value(row, col), 0), "entry"]
                    # 添加进列表
                    in_and_out_parking_list.append(car_time_info)
                # 如果是第三列，记录出场信息
                elif col == 2:
                    # 此时car_time_info如  {'英A0NF70': [datetime.datetime(2023, 6, 1, 11, 59, 56), 'exist']}

                    car_time_info[table.cell_value(row, col - 2)+"_"+str(xlrd.xldate_as_datetime(table.cell_value(row, col-1), 0))+"_"+str(xlrd.xldate_as_datetime(table.cell_value(row, col), 0))] = [xlrd.xldate_as_datetime(table.cell_value(row, col), 0), "exit"]
                    # 添加进列表
                    in_and_out_parking_list.append(car_time_info)

        # 此时列表如  [{'英A0NF70': [datetime.datetime(2023, 6, 1, 6, 18, 35), 'entry']},
        #           {'英A0NF70': [datetime.datetime(2023, 6, 1, 11, 59, 56), 'exist']}, ,,,,,]
        return in_and_out_parking_list

    """
    根据进或出场顺序进行排序
    """
    def sort_parking_time(self):
        # 读取excle
        in_and_out_parking_list = self.read_excel()
        # 根据进或出场顺序进行排序
        sorted_in_and_out_parking_list = sorted(in_and_out_parking_list, key=lambda x: list(x.values())[0][0])
        # 此时列表如  [{'英A0NF70': [datetime.datetime(2023, 6, 1, 6, 18, 35), 'entry']},
        # {'英AF15827': [datetime.datetime(2023, 6, 1, 7, 8, 56), 'entry']},, ]
        return sorted_in_and_out_parking_list

    """
    计算占用状态和费用
    """

    def cal_occupancy_and_fee(self):
        # 根据进或出场顺序进行排序
        sorted_in_and_out_parking_list = self.sort_parking_time()

        # 按时间顺序记录会被计费的车牌列表，遵循先进先出原则
        charging_car_queue = []
        # 车子的收费状态，记录包括，当前计费状态，开始计费时间，结束计费时间
        car_charging_status = dict()
        # 车子的收费数额，车牌号及对应的数额
        car_parking_fee = dict()

        # 遍历列表
        for item in sorted_in_and_out_parking_list:
            # 读取其中的plate和value list, 即 车牌号及其对应的进出场时间信息
            for plate, value_list in item.items():
                # 如果为入场车
                if value_list[1] == "entry":
                    # 如果此时有免费车位
                    if self.free_spots > 0:
                        # 免费车, 开始计费时间置为空，结束计费时间置为空
                        car_charging_status[plate] = ["free parking", value_list[0], None]
                        # 空余车位数
                        self.free_spots -= 1
                    # 此时无免费停车位
                    else:
                        # 计费车, 记录开始计费时间，结束计费时间暂时置为空
                        car_charging_status[plate] = ["charging parking", value_list[0], None]
                        # 按顺序添加收费车
                        charging_car_queue.append(plate)

                # 如果为出场车
                elif value_list[1] == "exit":
                    # 获取该车牌的收费状态信息
                    car_charging_status_list = car_charging_status.get(plate)
                    if car_charging_status_list is None:
                        print(f"Error: No entry record for car {plate}")
                        continue
                    # 车子的收费状态，是free parking--免费， 还是 charging parking --收费
                    charge_status = car_charging_status_list[0]
                    # 车子入场时间
                    car_plate_entry_time = car_charging_status_list[1]
                    # 车子停止计费时间
                    stop_charge_time = car_charging_status_list[2]
                    # 如果是完全免费车， 即 ["free parking", car_plate_entry_time, None]
                    if charge_status == "free parking" and car_plate_entry_time is not None and stop_charge_time is None:
                        # 车子收费0元
                        car_parking_fee[plate] = 0
                        # 当有免费车出场时，需要更新的所有状态
                        self.free_car_out_update_all_status(plate, value_list, car_charging_status, charging_car_queue)

                    # 如果是 免费车，但其实是更新过状态的， 即 ["free parking", car_plate_entry_time, stop_charge_time]
                    elif charge_status == "free parking" and car_plate_entry_time is not None and stop_charge_time is not None:
                        # 计算费用
                        parking_fee = self.calculate_fee(plate, car_plate_entry_time, stop_charge_time)
                        # 车子收费
                        car_parking_fee[plate] = parking_fee

                        # 当有免费车出场时，需要更新的所有状态
                        self.free_car_out_update_all_status(plate, value_list, car_charging_status, charging_car_queue)

                    # 如果是 彻底收费车， 即 ["charging parking", car_plate_entry_time, None]
                    elif charge_status == "charging parking" and car_plate_entry_time is not None and stop_charge_time is None:
                        # 出场时间
                        out_time = value_list[0]
                        # 计算费用
                        parking_fee = self.calculate_fee(plate, car_plate_entry_time, out_time)
                        # 车子收费
                        car_parking_fee[plate] = parking_fee
                        # 更新车辆收费状态，剔除该车
                        car_charging_status.pop(plate)

        return car_parking_fee

    """
    当有免费车出场时，需要更新的所有状态
    plate, 车牌号
    value_list, 车牌对应的进出场时间信息
    car_charging_status, 车子的收费状态，记录包括，当前计费状态，开始计费时间，结束计费时间
    charging_car_queue, 按时间顺序记录会被计费的车列表
    """

    def free_car_out_update_all_status(self, plate, value_list, car_charging_status, charging_car_queue):
        # 免费车位数增加1
        self.free_spots += 1
        # 更新车辆收费状态，剔除该车
        car_charging_status.pop(plate)
        # 如果 需要计费的车列表 不为空
        while len(charging_car_queue) >= 1:
            # 获取需要更改车辆收费状态的车牌号
            the_car_need_to_change_charge_status = charging_car_queue.pop(0)
            # 检查这辆车是否已经出场
            if the_car_need_to_change_charge_status not in car_charging_status:
                continue
            # 免费车位数减少1
            self.free_spots -= 1
            # 获取此时排在收费列表第一名的车牌的入场时间
            car_plate_entry_time = car_charging_status[the_car_need_to_change_charge_status][1]
            # 获取出场时间
            stop_charge_time = value_list[0]
            # 更新此时排在收费列表第一名的车牌状态，由收费改为免费，并记录此时的时间，作为出场时计费的根据
            car_charging_status[the_car_need_to_change_charge_status] = ["free parking", car_plate_entry_time,
                                                                         stop_charge_time]
            break
    def calculate_fee(self, plate, entry, exit):

        # 将停车时间转换为小时
        parking_time_hours = (exit - entry).total_seconds() / 3600
        fee = 0

        # 如果车位不是免费的，则按照收费标准计算费用
        if parking_time_hours <= 0.5:
            # 半小时以内不收费
            fee = 0
        elif parking_time_hours <= 1:
            # 1小时内收费4元
            fee = 4
        elif parking_time_hours <= 12:
            # 1小时以上至12小时内，每小时加收4元，封顶15元
            fee = min(4 * math.ceil(parking_time_hours), 15)
        elif parking_time_hours <= 24:
            # 12小时以上至24小时内，每小时加收4元，封顶25元
            fee = min(15 + 4 * math.ceil(parking_time_hours - 12), 25)
        else:
            # 超过24小时，按24小时循环收费，每24小时收费25元
            fee += 25 * (parking_time_hours // 24)
            remaining_hours = parking_time_hours % 24
            if remaining_hours <= 0.5:
                fee += 0
            elif remaining_hours <= 1:
                fee += 4
            elif remaining_hours <= 12:
                fee += min(4 * math.ceil(remaining_hours), 15)
            else:
                fee += min(4 * math.ceil(remaining_hours), 25)

        # 将费用四舍五入并限制在15块以内
        fee = min(round(fee), 15)
        #print(f"Fee for {plate}: {fee}")
        return fee

    """
    汇总费用
    """
    def details_and_sum_fee(self):
        car_parking_fee_dict = go.cal_occupancy_and_fee()
        total_fee = 0
        for key, values in car_parking_fee_dict.items():
            total_fee += car_parking_fee_dict[key]
        return car_parking_fee_dict, total_fee

go = ParkingCharge()
#go.read_excel()
result = go.details_and_sum_fee()
print(result)
