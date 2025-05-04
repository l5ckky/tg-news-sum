from loguru import logger
import datetime

logger.add(f'logs/daily/log_{datetime.date.today().strftime("%d_%m_%Y")}.log',
           level='DEBUG',
           format="{time:DD.MM.YYYY-HH:mm:ss.SSS} | {level} | {message}",
           rotation=datetime.timedelta(days=1))

logger.info("Пост {teefsg(mfreqe)} канала {awfwet81@(&#'']{}}{]][}ъэжХ1дфаб'HRNJT@#*&()J!@)_id)} содержит+/  fслово {wef;l/ и переслан в канал сводки")