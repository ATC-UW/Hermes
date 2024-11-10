class Logger:
    def __init__(self, log_file):
        self.log_file = log_file

    def log(self, message):
        with open(self.log_file, 'a') as f:
            f.write(message + '\n')

    def error(self, message):
        self.log(f'[ERROR]:   {message}')

    def warning(self, message):
        self.log(f'[WARNING]: {message}')

    def info(self, message):
        self.log(f'[INFO]:    {message}')

    def spacing(self):
        self.log('')
        self.log('------------------------------------------------------------')
        self.log('')

# [LOG]:     |
# [ERROR]:   |
# [WARNING]: |