import json
import datetime
import os


class Statistics:
    stats = {
        "today": {},
        "year": {}
    }

    def __init__(self):
        today = datetime.datetime.today().date().strftime("%d_%m_%Y")
        current_year = datetime.datetime.today().year

        self.year_stat_file = f"stats/yearly/stat_{str(current_year)}.json"
        self.today_stat_file = f"stats/daily/stat_{today}.json"

        if not os.path.exists(self.today_stat_file):
            with open(self.today_stat_file, 'w') as fp:
                pass
            # with open(self.today_stat_file, 'w+', encoding="utf-8") as file_today:
            #     file_today.close()
        if not os.path.exists(self.year_stat_file):
            with open(self.year_stat_file, 'w') as fp:
                pass
            # with open(self.year_stat_file, 'w+', encoding="utf-8") as file_today:
            #     file_today.close()

        with open(self.today_stat_file, 'r', encoding="utf-8") as file_today:
            with open(self.year_stat_file, 'r', encoding="utf-8") as file_cur_year:
                self.stats["today"] = json.load(file_today)
                self.stats["year"] = json.load(file_cur_year)
                file_cur_year.close()
            file_today.close()

    def record(self, word: str, channel: str):
        word = word.strip().lower()
        channel = channel.strip().lower()
        try:
            self.update()
            for i in ("today", "year"):
                self.stats[i]['total_posts'] += 1
                self.stats[i]['words_count'][word]['count'] += 1
                self.stats[i]['words_count'][word]['channels'][channel] += 1
                self.stats[i]['channels_count'][channel] += 1
                self.stats[i]['last_update'] = datetime.datetime.today().strftime("%d.%m.%Y-%H:%M:%S")

            with open(self.today_stat_file, 'w', encoding="utf-8") as file_today:
                with open(self.year_stat_file, 'w', encoding="utf-8") as file_cur_year:
                    json.dump(self.stats["today"], file_today)
                    json.dump(self.stats["year"], file_cur_year)
                    file_cur_year.close()
                file_today.close()
            return True
        except Exception as e:
            return False, e

    def update(self):
        with open(self.today_stat_file, 'r', encoding="utf-8") as file_today:
            with open(self.year_stat_file, 'r', encoding="utf-8") as file_cur_year:
                self.stats["today"] = json.load(file_today)
                self.stats["year"] = json.load(file_cur_year)
                file_cur_year.close()
            file_today.close()

    def get(self):
        return self.stats
