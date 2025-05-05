import json
import datetime
import os


# import stats


class Statistics:
    stats = {
        "today": {},
        "year": {}
    }

    def __init__(self):
        self.today = datetime.datetime.today().date().strftime("%d_%m_%Y")
        self.current_year = datetime.datetime.today().year

        self.year_stat_file = f"stats/yearly/stat_{str(self.current_year)}.json"
        self.today_stat_file = f"stats/daily/stat_{self.today}.json"

        if not os.path.exists(self.today_stat_file):
            if not os.path.exists("stats"):
                os.mkdir("stats")
            if not os.path.exists("stats/daily"):
                os.mkdir("stats/daily")
            with open(self.today_stat_file, 'w') as fp:
                fp.write("{}")
        if not os.path.exists(self.year_stat_file):
            if not os.path.exists("stats"):
                os.mkdir("stats")
            if not os.path.exists("stats/yearly"):
                os.mkdir("stats/yearly")
            with open(self.year_stat_file, 'w') as fp:
                fp.write("{}")

        with open(self.today_stat_file, 'r', encoding="utf-8") as file_today:
            with open(self.year_stat_file, 'r', encoding="utf-8") as file_cur_year:
                self.stats["today"] = json.load(file_today)
                self.stats["year"] = json.load(file_cur_year)
                file_cur_year.close()
            file_today.close()

        print(self.stats)

    def record(self, word: str, channel: str):
        word = word.strip().lower()
        channel = channel.strip().lower()
        self.update()
        for i in ("today", "year"):
            if self.stats[i] != {}:
                self.stats[i]['total_posts'] += 1
                if self.stats[i]['words_count'].get(word, {}):
                    self.stats[i]['words_count'][word]['count'] += 1
                else:
                    self.stats[i]['words_count'][word] = {"count": 1, "channels": {}}
                self.stats[i]['words_count'][word]['count'] += 1
                if self.stats[i]['words_count'][word]['channels'].get(channel, {}):
                    self.stats[i]['words_count'][word]['channels'][channel] += 1
                else:
                    self.stats[i]['words_count'][word]['channels'][channel] = 1
                if self.stats[i]['channels_count'].get(channel, {}):
                    self.stats[i]['channels_count'][channel] += 1
                else:
                    self.stats[i]['channels_count'][channel] = 1
                self.stats[i]['last_update'] = datetime.datetime.today().strftime("%d.%m.%Y-%H:%M:%S")
            else:
                self.stats[i] = {
                    f"{'date' if i == 'today' else 'year'}": self.today if i == 'today' else self.current_year,
                    "last_update": datetime.datetime.today().strftime("%d.%m.%Y-%H:%M:%S"),
                    "total_processed_words": None,
                    "total_posts": 1,
                    "words_count": {},
                    "channels_count": {}
                }
                self.stats[i]['words_count'][word] = {}
                self.stats[i]['words_count'][word]['count'] = 1
                self.stats[i]['words_count'][word]['channels'] = {"channel": 1}
                self.stats[i]['channels_count'][channel] = 1
                # self.stats[i]['last_update'] = datetime.datetime.today().strftime("%d.%m.%Y-%H:%M:%S")
        print(self.stats)
        with open(self.today_stat_file, 'w', encoding="utf-8") as file_today:
            with open(self.year_stat_file, 'w', encoding="utf-8") as file_cur_year:
                json.dump(self.stats["today"], file_today)
                json.dump(self.stats["year"], file_cur_year)
                file_cur_year.close()
            file_today.close()
        return True

    def update(self):
        self.today = datetime.datetime.today().date().strftime("%d_%m_%Y")
        self.current_year = datetime.datetime.today().year

        self.year_stat_file = f"stats/yearly/stat_{str(self.current_year)}.json"
        self.today_stat_file = f"stats/daily/stat_{self.today}.json"

        with open(self.today_stat_file, 'r', encoding="utf-8") as file_today:
            with open(self.year_stat_file, 'r', encoding="utf-8") as file_cur_year:
                self.stats["today"] = json.load(file_today)
                self.stats["year"] = json.load(file_cur_year)
                file_cur_year.close()
            file_today.close()


def get(self):
    return self.stats


if __name__ == "__main__":
    st = Statistics()
    st.record("test_word", "test_channel")
