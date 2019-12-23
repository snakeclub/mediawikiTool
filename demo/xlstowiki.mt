{
    "AMT{ns}错误码开发规范{sub}错误码清单": {
        "description": "错误码清单",
        "show_all_sheet": false,
        "sheet_index_list": [0],
        "sheet_name_list": [],
        "default_para": {
            "has_head": true,
            "head_row": 0,
            "data_row_start": 3,
            "data_row_end": -1,
            "data_col_start": 0,
            "data_cols_end": -1,
            "col_filter": [8, 9, 3, 10, 7, 6, 4, 1, 2],
            "head_trans_dict": {
                "标准错误码(必填)": "标准错误码",
                "维护人(必填)": "维护人",
                "维护日期(必填)": "维护日期"
            },
            "col_trans_dict": {
                "8": {
                    "0": "成功类",
                    "1": "用户行为类",
                    "2": "网络通讯类",
                    "3": "数据库类",
                    "4": "操作系统类",
                    "5": "函数调用类",
                    "6": "应用服务类",
                    "7": "业务错误类",
                    "8": "其他类"
                },
                "9": {
                    "0": "账户",
                    "1": "用户",
                    "2": "产品",
                    "3": "机构柜员",
                    "4": "公共",
                    "5": "批量"
                }
            }
        },
        "sheet_index_para_list": {},
        "sheet_name_para_list": {}
    },
    "AMT{ns}接口开发规范{sub}交易码清单": {
        "description": "交易码清单",
        "show_all_sheet": false,
        "sheet_index_list": [0],
        "sheet_name_list": [],
        "default_para": {
            "has_head": true,
            "head_row": 0,
            "data_row_start": 3,
            "data_row_end": -1,
            "data_col_start": 0,
            "data_cols_end": -1,
            "col_filter": [2, 3, 7, 8, 4, 5],
            "head_trans_dict": {
                "交易类别(必填)": "交易类别",
                "标准交易码(必填)": "标准交易码",
                "维护人(必填)": "维护人",
                "维护日期(必填)": "维护日期"
            },
            "col_trans_dict": {
                "2": {
                    "01": "协议类",
                    "02": "查询类",
                    "03": "资金变动类",
                    "04": "资金冲正类",
                    "05": "配置管理类",
                    "06": "权限设置类",
                    "07": "异常处理类",
                    "08": "密钥安全类",
                    "09": "开户类",
                    "10": "文件类",
                    "11": "通知类"
                }
            }
        },
        "sheet_index_para_list": {},
        "sheet_name_para_list": {}
    },
    "AMT{ns}全行应用系统清单": {
        "description": "全行应用系统清单",
        "show_all_sheet": false,
        "sheet_index_list": [0],
        "sheet_name_list": [],
        "default_para": {
            "has_head": true,
            "head_row": 0,
            "data_row_start": 3,
            "data_row_end": -1,
            "data_col_start": 0,
            "data_cols_end": -1,
            "col_filter": [1, 3, 4, 7, 5, 9, 10, 11, 18],
            "head_trans_dict": {
                "系统(必填)": "一级系统",
                "系统简称(必填)": "一级系统标识",
                "子系统(必填)": "系统",
                "子系统中文简称": "习惯叫法",
                "子系统简称(必填)": "系统标识",
                "所属组(必填)": "所属组",
                "项目经理(必填)": "项目经理",
                "应用系统状态(必填)": "上线状态",
                "业务主管部门(必填)": "业务主管部门"
            },
            "col_trans_dict": {}
        },
        "sheet_index_para_list": {},
        "sheet_name_para_list": {}
    }
}