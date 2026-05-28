import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation


class StockAnalytics:

    def __init__(self, filepath: str = None, dataframe=None, starting_balance=10000):

        pd.set_option('float_format', '{:.2f}'.format)
        pd.set_option('display.max_columns', 100)

        if dataframe is None:
            self.data = self.__load_data(filepath)
        else:
            self.data = dataframe.copy()
            self.__transform_data()

        self.starting_balance = starting_balance
        self.balance = starting_balance
        self.transactions = pd.DataFrame(
            columns=['open_date', 'open_price', 'amount', 'close_date', 'close_price', 'profit', 'commision',
                     'balance'])
        self.has_opened_position = False

    def __load_data(self, filepath: str) -> pd.DataFrame:

        df = pd.read_csv(filepath)
        self.__transform_data(df)

        return df

    def __transform_data(self) -> None:
        self.data['<DATE>'] = pd.to_datetime(self.data['<DATE>'], format='%Y%m%d')
        self.data['<DATE>'] = self.data['<DATE>'].dt.date

    def add_moving_average(self, periods: int) -> str:
        """ :param periods number of periods for moving average
            :returns string with name of the moving average in format ma{periods}
        """

        # moving average
        self.data[f'<MA{periods}>'] = self.data['<CLOSE>'].rolling(periods).mean()

        return f'ma{periods}'

    def calculate_commision(self, transaction_value: float) -> float:
        min_commision = 5.0
        base_pct = 0.0039

        if transaction_value * base_pct < min_commision:
            return min_commision
        else:
            return transaction_value * base_pct

    def simulate_stock(self, conds: dict) -> pd.DataFrame:
        # define opening and closing params
        # position is being opened when the price breaks through the MA from the bottom
        # position is being closed when the price breaks through the MA from the top
        prev_row = {'open': 0, 'close': 0}
        prev_row.update(dict.fromkeys(conds.values(), 0))
        transaction = dict.fromkeys(self.transactions.columns, 0)

        # model 1 - open on going up through MA100, close on MA26

        for ind in range(len(self.data.index)):
            # if prev_row['close'] > prev_row[conds['open_cond']] and not self.has_opened_position:
            # checking if ma's are not equal to 0
            if 0 not in prev_row.values():
                if (ind > 1 and self.data[f"<{conds['close_cond'].upper()}>"].iloc[ind-2] < prev_row[conds['open_cond']]) and prev_row[conds['close_cond']] > prev_row[conds['open_cond']] and not self.has_opened_position:
                    # open new position
                    self.has_opened_position = True
                    transaction['open_date'] = self.data['<DATE>'].iloc[ind]
                    transaction['open_price'] = self.data['<OPEN>'].iloc[ind]
                    transaction['amount'] = self.balance // transaction['open_price']

                    # stop at insufficient funds
                    if transaction['amount'] <= 0:
                        break

                    transaction['commision'] = self.calculate_commision(
                        transaction['amount'] * transaction['open_price'])
                    self.balance -= transaction['commision']
                elif (ind > 1 and self.data['<CLOSE>'].iloc[ind-2] > prev_row[conds['open_cond']]) and prev_row['close'] < prev_row[conds['open_cond']] and self.has_opened_position:
                    # elif prev_row['close'] < prev_row[conds['close_cond']] and self.has_opened_position:
                    # close position
                    self.has_opened_position = False
                    transaction['close_date'] = self.data['<DATE>'].iloc[ind]
                    transaction['close_price'] = self.data['<OPEN>'].iloc[ind]
                    profit = (transaction['close_price'] - transaction['open_price']) * transaction['amount']
                    transaction['profit'] = profit
                    transaction['commision'] = self.calculate_commision(
                        transaction['amount'] * transaction['close_price'])
                    # update balance
                    self.balance += (profit - transaction['commision'])
                    transaction['balance'] = self.balance
                    # insert row into transactions df
                    self.transactions.loc[len(self.transactions)] = list(transaction.values())
                    # reset transaction data
                    transaction = dict.fromkeys(self.transactions.columns, 0)

            # set prev row values
            prev_row['open'] = self.data['<OPEN>'].iloc[ind]
            prev_row['close'] = self.data['<CLOSE>'].iloc[ind]
            prev_row[conds['open_cond']] = self.data[f"<{conds['open_cond'].upper()}>"].iloc[ind]
            prev_row[conds['close_cond']] = self.data[f"<{conds['close_cond'].upper()}>"].iloc[ind]

        # add open transaction
        if self.has_opened_position:
            self.transactions.loc[len(self.transactions)] = list(transaction.values())

        print(f"Wynik modelu dla {self.data['<TICKER>'].iloc[0]}")
        print(f'Końcowy balance: {self.balance: .2f}')
        final_profit = self.balance - self.starting_balance
        print(f'Total profit: {final_profit:.2f}, ptc: {final_profit / self.starting_balance * 100: .2f} %')
        print(f"Total commision paid: {self.transactions['commision'].sum()}")
        print(self.transactions)

        if len(self.transactions) > 0:
            self.transactions['balance'].plot()
            plt.title(f"Analiza {self.data['<TICKER>'].iloc[0]}")
            plt.show()
        # self.transactions.to_csv('result_v1.csv')

        return self.transactions


def animate_plot(data: pd.DataFrame, averages_to_plot: list, transactions: pd.DataFrame):
    # print(df.head())
    # print(df.info())

    fig, ax = plt.subplots()
    ann = True

    x = data['<DATE>'].iloc[0:20]
    line, = ax.plot(x, data['<CLOSE>'].iloc[0:20].values)
    lines = []
    for avg_name in averages_to_plot:
        line2, = ax.plot(x, data[f'<{avg_name}>'].iloc[0:20].values)
        lines.append(line2)

    def animate(i):
        x_data = data['<DATE>'].iloc[0:20 + i]
        y_data = data['<CLOSE>'].iloc[0:20 + i].values
        line.set_data(x_data, y_data)

        # plotting lines to show entry points
        # for ind in transactions.index:
        #     if transactions['open_date'][ind] in x_data.values:
        #         plt.axvline(transactions['open_date'][ind], color='#66aa66')
        #     if transactions['close_date'][ind] in x_data.values:
        #         plt.axvline(transactions['close_date'][ind], color='#aa4444')
        #     else:
        #         break
        # if ann:
        #     ax.annotate("", xy=(x_data[19 + i], y_data[19 + i]), xytext=(0, 0), arrowprops=dict(arrowstyle="-^"))

        for ma_line_name, ma_line in zip(averages_to_plot, lines):
            ma_data = data[f'<{ma_line_name}>'].iloc[0:20 + i].values
            ma_line.set_data(x_data, ma_data)

        line.axes.axis([x_data.min(), x_data.max(), 0, max(y_data) * 1.3])
        line.axes.set_ylim([0, max(y_data) * 1.3])

        # plt.legend()

        return [line] + lines

    ani = animation.FuncAnimation(
        fig, animate, interval=100, blit=False, save_count=100)

    plt.show()


if __name__ == '__main__':
    # path = './data/pkn.txt'

    # loop for all tickers in dataframe

    initial_data = pd.read_csv('wse_stocks.csv', index_col=0)
    initial_data.drop(columns=['TYPE'], inplace=True)
    # data.set_index('<TICKER>', inplace=True)

    # temporary ticker list
    ticker_list = ['PKN', 'KGH']

    # for ticker in initial_data['<TICKER>'].unique().tolist():
    for ticker in ticker_list:
        simulator = StockAnalytics(dataframe=initial_data[initial_data['<TICKER>'] == ticker])
        trans = simulator.simulate_stock({
            'open_cond': simulator.add_moving_average(52),
            'close_cond': simulator.add_moving_average(26)
        })

    # # testing on other data
    # data = pd.read_csv(path, index_col=0)
    # # filtered data
    # data = data[data['<TICKER>'] == 'KGH']
    # data.drop(columns=['TYPE'], inplace=True)
    # data.set_index('<TICKER>', inplace=True)
    # data.to_csv('kgh.csv')
    # print(data.head())
    # exit()



    # simulator = StockAnalytics(path)
    # # simulator = StockAnalytics(path)
    # trans = simulator.simulate_stock({
    #     'open_cond': simulator.add_moving_average(200),
    #     'close_cond': simulator.add_moving_average(52)
    # })
    #
    animate_plot(simulator.data, ['MA26', 'MA52'], trans)
