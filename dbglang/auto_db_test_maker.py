from random import shuffle, randint
from typing import Generator
from itertools import permutations


class TestGenerateSession:
    name_str_gen: Generator
    text_str_gen: Generator
    info_str_gen: Generator
    int_stream: Generator

    def __new__(cls, *args, **kwargs):

        cls.name_str_gen = cls.str_inst_generator_maker(4)
        cls.text_str_gen = cls.str_inst_generator_maker(5)
        cls.info_str_gen = cls.str_inst_generator_maker(6)

        cls.int_stream = cls.int_inst_generator_maker()
        return cls

    @classmethod
    def int_inst_generator_maker(cls):
        i = 1
        while True:
            yield i
            i += 1

    @classmethod
    def str_inst_generator_maker(cls, n: int):
        words = permutations(
            set('苟利国家生死以岂因福祸避趋之安能摧眉折腰事学霸使我不得玩贪玩蓝月厅下如积水空明水中藻荇交横盖橘子皮也独秀清末民初人也名声噪于李大钊前排而挡其黑板也故世人称独秀请你下来也'), n)
        for each in words:
            yield '"' + ''.join(each) + '"'

    @classmethod
    def time_inst_maker(cls, n):
        return f'datetime.now() - timedelta(minutes = 42 * {n})'

    @classmethod
    def enum_inst_maker(cls, type_name: str):
        return f'{type_name}(randint(1, len({type_name})))'

    @classmethod
    def generate_inst_for_type(cls, x: str):

        if x == 'Integer':
            return next(cls.int_stream)
        elif x.startswith('String('):
            i = x[7:10]
            return {'20)': lambda: next(cls.name_str_gen),
                    '50)': lambda: next(cls.text_str_gen),
                    '200': lambda: next(cls.info_str_gen),
                    '500': lambda: next(cls.info_str_gen)}[i]()
        elif x.startswith('Date'):
            return cls.time_inst_maker(randint(1, 23))
        else:
            return cls.enum_inst_maker(x)
