import os
import time
import random
import math
import requests
import json
import pandas as pd
import logging
from tqdm import tqdm
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 定义常量
SAVE_PATH = r"F:\collection_spb_info\GJ\QXG"
BASE_NAME = os.getenv('BASE_NAME')

# 确保保存路径存在
os.makedirs(SAVE_PATH, exist_ok=True)
logger.info(f"保存路径设置为: {SAVE_PATH}")

# 请求头
img_header = {
    "Accept": os.getenv("ACCEPT"),
    "Accept-Encoding": os.getenv("ACCEPT_ENCODING"),
    "Accept-Language": os.getenv("ACCEPT_LANGUAGE"),
    "Authorization": os.getenv("AUTHORIZATION"),
    "Connection": os.getenv("CONNECTION"),
    "Content-Length": os.getenv("CONTENT_LENGTH"),
    "Content-Type": os.getenv("CONTENT_TYPE"),
    "Cookie": os.getenv("COOKIE"),
    "Host": os.getenv("HOST"),
    "origin": os.getenv("ORIGIN"),
    "Referer": os.getenv("REFERER"),
    "Sec-Ch-Ua": os.getenv("SEC_CH_UA"),
    "Sec-Ch-Ua-Mobile": os.getenv("SEC_CH_UA_MOBILE"),
    "Sec-Ch-Ua-Platform": os.getenv("SEC_CH_UA_PLATFORM"),
    "Sec-Fetch-Dest": os.getenv("SEC_FETCH_DEST"),
    "Sec-Fetch-Mode": os.getenv("SEC_FETCH_MODE"),
    "Sec-Fetch-Site": os.getenv("SEC_FETCH_SITE"),
    "User-Agent": os.getenv("USER_AGENT")
}
header = {
    "Accept": os.getenv("ACCEPT"),
    "Accept-Encoding": os.getenv("ACCEPT_ENCODING"),
    "Accept-Language": os.getenv("ACCEPT_LANGUAGE"),
    "Authorization": os.getenv("AUTHORIZATION"),
    "Connection": os.getenv("CONNECTION"),
    "Cookie": os.getenv("COOKIE"),
    "Host": os.getenv("HOST"),
    "Referer": os.getenv("REFERER"),
    "Sec-Ch-Ua": os.getenv("SEC_CH_UA"),
    "Sec-Ch-Ua-Mobile": os.getenv("SEC_CH_UA_MOBILE"),
    "Sec-Ch-Ua-Platform": os.getenv("SEC_CH_UA_PLATFORM"),
    "Sec-Fetch-Dest": os.getenv("SEC_FETCH_DEST"),
    "Sec-Fetch-Mode": os.getenv("SEC_FETCH_MODE"),
    "Sec-Fetch-Site": os.getenv("SEC_FETCH_SITE"),
    "User-Agent": os.getenv("USER_AGENT")
}

# 辅助函数
def retry_if_no_return(func):
    def wrapper(*args, **kwargs):
        retry_times = 5
        while retry_times >= 0:
            result = func(*args, **kwargs)
            if result:
                return result
            logger.warning(f"函数 {func.__name__} 执行失败，正在重试...")
            time.sleep(2)
            retry_times -= 1
        logger.error(f"函数 {func.__name__} 重试 5 次后仍然失败")
    return wrapper

@retry_if_no_return
def download_image(url, save_path_name, headers):
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            with open(save_path_name, 'wb') as f:
                f.write(r.content)
            logger.info(f"图片已保存: {save_path_name}")
            return True
    except Exception as e:
        logger.error(f"下载图片失败: {str(e)}")
        return False
    time.sleep(random.random())

def get_today_date():
    return datetime.today().strftime("%Y%m%d")

# API请求函数
def api_request(url, method='GET', headers=None, params=None, data=None):
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method == 'POST':
            response = requests.post(url, headers=headers, data=json.dumps(data))
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"请求失败，状态码：{response.status_code}")
            return None
    except Exception as e:
        logger.error(f"请求出错：{str(e)}")
        return None

# 数据获取函数
def get_city_code(code, headers):
    url = os.getenv('CITY_CODE_URL')
    return api_request(url, headers=headers, params={'code': code})

def get_gj_info_total(code, headers, **kwargs):
    url = os.getenv('QCZS_URL')
    params = {
        'pageNum': 1,
        'pageSize': 50,
        'xzqdm': code,
        **kwargs
    }
    result_list = []
    response = api_request(url, headers=headers, params=params)
    if response and 'result' in response:
        total = response['result']['total']
        page_num = math.ceil(total / 50)
        for i in range(1, page_num + 1):
            params['pageNum'] = i
            page_response = api_request(url, headers=headers, params=params)
            if page_response and 'result' in page_response:
                result_list += page_response['result']['records']
    logger.info(f"获取到 {len(result_list)} 条信息")
    return result_list

def get_point_info(point_id, info_type, headers):
    url_mapping = {
        'sf': os.getenv('SF_URL'),
        'img': os.getenv('IMG_URL'),
        'ldtj': os.getenv('LDTJ_URL'),
        'base': os.getenv('JBXX_URL'),
        'ctd': os.getenv('CTD_URL'),
        'pm': os.getenv('PM_URL'),
        'pmfc': os.getenv('PM_FC_URL')
    }
    url = url_mapping.get(info_type)
    if not url:
        logger.error(f"未知的信息类型: {info_type}")
        return None
    
    if info_type == 'img':
        return api_request(url, method='POST', headers=headers, data={"glbh": str(int(point_id))})
    else:
        return api_request(f"{url}{point_id}", headers=headers)

# 主函数
def main():
    logger.info("开始执行主函数")
    
    # 配置浏览器
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", "localhost:9998")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(60)
    logger.info("浏览器配置完成")

    # 更新headers
    headers = header
    img_headers = img_header

    # 获取基本信息
    info_list = get_gj_info_total(code=520502, headers=headers)
    df_base_info = pd.DataFrame(info_list)
    base_info_path = os.path.join(SAVE_PATH, f'base_info_{get_today_date()}_{len(info_list)}.xlsx')
    df_base_info.to_excel(base_info_path, index=False)
    logger.info(f"基本信息已保存到: {base_info_path}")

    # 区分样点类别
    pm_list = df_base_info[df_base_info['ydlb'] == '1']['ydbh'].to_list()
    bc_list = df_base_info[df_base_info['ydlb'] == '0']['ydbh'].to_list()
    loop_all_point = bc_list + pm_list
    logger.info(f"总共 {len(loop_all_point)} 个样点，其中剖面点 {len(pm_list)} 个，标准点 {len(bc_list)} 个")

    # 获取并保存各种信息
    info_types = ['img', 'ldtj', 'ctd', 'sf']
    for info_type in info_types:
        logger.info(f"开始获取 {info_type} 信息")
        info_list = []
        for point in tqdm(loop_all_point, desc=f"处理 {info_type} 信息"):
            point_info = get_point_info(point, info_type, headers if info_type != 'img' else img_headers)
            if point_info and 'result' in point_info:
                if isinstance(point_info['result'], list):
                    info_list.extend(point_info['result'])
                else:
                    info_list.append(point_info['result'])
            time.sleep(random.random())
        
        df_info = pd.DataFrame(info_list)
        info_path = os.path.join(SAVE_PATH, f'{info_type}_info_{get_today_date()}_{len(loop_all_point)}.xlsx')
        df_info.to_excel(info_path, index=False)
        logger.info(f"{info_type} 信息已保存到: {info_path}")

    # 获取剖面信息
    logger.info("开始获取剖面信息")
    pm_info_list = []
    pm_fc_info_list = []
    for point in tqdm(pm_list, desc="处理剖面信息"):
        pm_info = get_point_info(point, 'pm', headers)
        if pm_info and 'result' in pm_info:
            pm_info_list.append(pm_info['result'])
        
        pm_fc_info = get_point_info(point, 'pmfc', headers)
        if pm_fc_info and 'result' in pm_fc_info:
            pm_fc_info_list.extend(pm_fc_info['result'])
        
        time.sleep(random.random())

    df_pm_info = pd.DataFrame(pm_info_list)
    pm_info_path = os.path.join(SAVE_PATH, f'pm_info_{get_today_date()}_{len(pm_info_list)}.xlsx')
    df_pm_info.to_excel(pm_info_path, index=False)
    logger.info(f"剖面信息已保存到: {pm_info_path}")

    df_pm_fc_info = pd.DataFrame(pm_fc_info_list)
    pm_fc_info_path = os.path.join(SAVE_PATH, f'pm_fc_info_{get_today_date()}_{len(pm_fc_info_list)}.xlsx')
    df_pm_fc_info.to_excel(pm_fc_info_path, index=False)
    logger.info(f"剖面分层信息已保存到: {pm_fc_info_path}")

    logger.info("主函数执行完毕")

if __name__ == "__main__":
    main()