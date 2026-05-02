from storage import save_presets
from datetime import date

def user_presets():
    data_plan = input("Enter carrier and plan (e.g MTN 1gb daily): ")
    usage_limit = int(input("Enter Data Limit in mb (e.g 500): "))
    current_date = str(date.today())
    presets = [{"data_plan":data_plan,"usage_limits":usage_limit, "date":current_date}]
    save_presets(presets)



    