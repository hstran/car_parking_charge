                                               某公司停车收费系统







1. 某公司有83个免费停车位，但是开车的人远不止83个，所有费用由公司买单，所以本项目的主要解决问题就是计算出每天或者每个月公司要付的额外停车费。
2. 本项目涉及到的几个问题包括免费停车位总容量只有83个，有车进来也必然有车出去。当有免费停车位的车走出车库，就会有另一辆正在收费的车被停止计费。
3. 对于是否免费，在进车库的时候就已经决定了。
4. 对于跨天停车的车辆，如果一开始就占据了免费停车位，只要不出车库就一直占据免费停车位也就一直会是免费的。如果一开始是收费的，只要总容量低于了83辆则会停止后续收费，那么无论停多少天，都只有停止收费前的费用。
5. 本项目通过excel表格记录车牌号码，入场时间，出场时间这三项来计算停车费用。具体代码以及少量数据表格可以读取。
