import re
from dataclasses import dataclass
from typing import List, Tuple

import pandas as pd
import streamlit as st


@dataclass
class LZ77Token:
    offset: int
    length: int
    next_char: str

    def __str__(self):
        char_display = repr(self.next_char) if self.next_char else "''"
        return f"({self.offset}, {self.length}, {char_display})"

    def to_tuple(self) -> Tuple[int, int, str]:
        return self.offset, self.length, self.next_char


class LZ77Encoder:

    def __init__(self, dictionary_size: int = 4096, buffer_size: int = 18):
        self.dictionary_size = dictionary_size
        self.buffer_size = buffer_size

    def encode(self, text: str) -> List[LZ77Token]:
        if not text:
            return []

        tokens = []
        pos = 0

        while pos < len(text):
            best_offset = 0
            best_length = 0

            dict_start = max(0, pos - self.dictionary_size)
            lookahead_end = min(pos + self.buffer_size, len(text))

            for i in range(dict_start, pos):
                length = 0
                while (
                    pos + length < lookahead_end
                    and length < self.buffer_size
                    and text[i + length] == text[pos + length]
                ):
                    length += 1

                if length > best_length:
                    best_length = length
                    best_offset = pos - i

            next_pos = pos + best_length
            next_char = text[next_pos] if next_pos < len(text) else ""

            tokens.append(LZ77Token(
                offset=best_offset,
                length=best_length,
                next_char=next_char
            ))

            pos = next_pos + 1

        return tokens

    def get_encoding_steps(self, text: str) -> List[dict]:
        if not text:
            return []

        steps = []
        pos = 0
        step_num = 1

        while pos < len(text):
            best_offset = 0
            best_length = 0

            dict_start = max(0, pos - self.dictionary_size)
            lookahead_end = min(pos + self.buffer_size, len(text))

            dictionary = text[dict_start:pos]
            lookahead = text[pos:lookahead_end]

            for i in range(dict_start, pos):
                length = 0
                while (
                    pos + length < lookahead_end
                    and length < self.buffer_size
                    and text[i + length] == text[pos + length]
                ):
                    length += 1

                if length > best_length:
                    best_length = length
                    best_offset = pos - i

            next_pos = pos + best_length
            next_char = text[next_pos] if next_pos < len(text) else ""
            matched_string = text[pos:pos + best_length] if best_length > 0 else ""

            steps.append({
                "step": step_num,
                "position": pos,
                "dictionary": dictionary if dictionary else "(пусто)",
                "lookahead": lookahead,
                "match": matched_string if matched_string else "(нет)",
                "offset": best_offset,
                "length": best_length,
                "next_char": repr(next_char) if next_char else "(конец)",
                "token": f"({best_offset}, {best_length}, {repr(next_char) if next_char else ''})"
            })

            pos = next_pos + 1
            step_num += 1

        return steps


class LZ77Decoder:

    def decode(self, tokens: List[LZ77Token]) -> str:
        result = []

        for token in tokens:
            if token.offset > 0 and token.length > 0:
                start_pos = len(result) - token.offset
                for i in range(token.length):
                    result.append(result[start_pos + i])

            if token.next_char:
                result.append(token.next_char)

        return "".join(result)

    def get_decoding_steps(self, tokens: List[LZ77Token]) -> List[dict]:
        steps = []
        result = []

        for i, token in enumerate(tokens):
            added_chars = []

            if token.offset > 0 and token.length > 0:
                start_pos = len(result) - token.offset
                for j in range(token.length):
                    char = result[start_pos + j]
                    result.append(char)
                    added_chars.append(char)

            if token.next_char:
                result.append(token.next_char)
                added_chars.append(token.next_char)

            if token.offset > 0:
                action = (
                    f"Копирование {token.length} символов с позиции -{token.offset} "
                    f"и добавление символа {repr(token.next_char)}"
                    if token.next_char
                    else f"Копирование {token.length} символов с позиции -{token.offset}"
                )
            else:
                action = f"Добавление символа {repr(token.next_char)}"

            steps.append({
                "step": i + 1,
                "token": str(token),
                "action": action,
                "added": "".join(added_chars),
                "result": "".join(result)
            })

        return steps


def parse_tokens_from_string(token_string: str) -> List[LZ77Token]:
    tokens = []
    pattern = r"\((\d+),\s*(\d+),\s*[\'\"]([^\'\"]*)[\'\"]?\)"
    matches = re.findall(pattern, token_string)

    for match in matches:
        offset = int(match[0])
        length = int(match[1])
        next_char = match[2]
        tokens.append(LZ77Token(offset, length, next_char))

    return tokens


def calculate_compression_ratio(original: str, tokens: List[LZ77Token]) -> dict:
    original_bits = len(original) * 8
    token_bits = len(tokens) * 24

    compression_ratio = original_bits / token_bits if token_bits > 0 else 0
    space_saving = (1 - token_bits / original_bits) * 100 if original_bits > 0 else 0

    return {
        "original_size": len(original),
        "original_bits": original_bits,
        "num_tokens": len(tokens),
        "encoded_bits": token_bits,
        "compression_ratio": compression_ratio,
        "space_saving": space_saving
    }


def apply_styles():
    st.markdown("""
        <style>
            .block-container {
                padding-top: 1.5rem;
                padding-bottom: 2rem;
            }
            h1, h2, h3 {
                font-weight: 600;
            }
            section[data-testid="stSidebar"] {
                background-color: #f5f5f7;
            }
            div[data-testid="metric-container"] {
                background-color: #fafafa;
                border: 1px solid #e6e6e6;
                padding: 10px;
                border-radius: 6px;
            }
            .app-note {
                padding: 12px 14px;
                border: 1px solid #dddddd;
                border-radius: 6px;
                background-color: #fafafa;
                margin-bottom: 1rem;
            }
        </style>
    """, unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="LZ77: кодирование и декодирование",
        layout="wide"
    )

    apply_styles()

    st.title("LZ77: словарное кодирование и декодирование")

    st.markdown("""
    <div class="app-note">
        Алгоритм LZ77 использует скользящее окно, состоящее из словаря
        (уже обработанной части текста) и буфера предпросмотра
        (части текста, подлежащей кодированию).
        <br><br>
        Формат токена: <b>(смещение, длина, следующий_символ)</b>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.header("Параметры")

    dictionary_size = st.sidebar.slider(
        "Размер словаря",
        min_value=4,
        max_value=4096,
        value=256,
        help="Максимальное количество символов в окне поиска"
    )

    buffer_size = st.sidebar.slider(
        "Размер буфера",
        min_value=2,
        max_value=256,
        value=16,
        help="Максимальное количество символов для поиска совпадения"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **Пояснения**

    - Смещение — расстояние назад до начала совпадения
    - Длина — количество совпавших символов
    - Следующий символ — символ после совпадения
    """)

    tab1, tab2 = st.tabs(["Кодирование", "Декодирование"])

    with tab1:
        st.header("Кодирование текста")

        input_text = st.text_area(
            "Введите текст для кодирования",
            value="ABRACADABRA",
            height=120,
            key="encode_input"
        )

        encode_button = st.button("Закодировать", type="primary", key="encode_btn")

        if encode_button:
            if not input_text:
                st.warning("Введите текст для кодирования.")
            else:
                encoder = LZ77Encoder(dictionary_size, buffer_size)
                tokens = encoder.encode(input_text)

                st.subheader("Результат кодирования")

                tokens_str = ", ".join(str(t) for t in tokens)
                st.code(tokens_str, language=None)
                st.text_input("Токены для копирования", value=tokens_str, key="encoded_result")

                stats = calculate_compression_ratio(input_text, tokens)

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Исходный размер", f"{stats['original_size']} симв.")
                col2.metric("Количество токенов", stats["num_tokens"])
                col3.metric("Коэффициент сжатия", f"{stats['compression_ratio']:.2f}")
                col4.metric("Экономия места", f"{stats['space_saving']:.1f}%")

                st.subheader("Пошаговый процесс кодирования")

                steps = encoder.get_encoding_steps(input_text)
                df = pd.DataFrame(steps)
                df.columns = [
                    "Шаг", "Позиция", "Словарь", "Буфер", "Совпадение",
                    "Смещение", "Длина", "Следующий символ", "Токен"
                ]
                st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        st.header("Декодирование токенов")

        default_tokens = "(0, 0, 'A'), (0, 0, 'B'), (0, 0, 'R'), (3, 1, 'C'), (2, 1, 'D'), (7, 4, '')"

        tokens_input = st.text_area(
            "Введите токены для декодирования",
            value=default_tokens,
            height=120,
            help="Формат: (смещение, длина, 'символ'), ...",
            key="decode_input"
        )

        decode_button = st.button("Декодировать", type="primary", key="decode_btn")

        if decode_button:
            if not tokens_input:
                st.warning("Введите токены для декодирования.")
            else:
                try:
                    tokens = parse_tokens_from_string(tokens_input)

                    if not tokens:
                        st.error("Не удалось распознать токены. Проверьте формат ввода.")
                    else:
                        decoder = LZ77Decoder()
                        decoded_text = decoder.decode(tokens)

                        st.subheader("Результат декодирования")
                        st.code(decoded_text, language=None)
                        st.text_input(
                            "Декодированный текст для копирования",
                            value=decoded_text,
                            key="decoded_result"
                        )

                        st.subheader("Пошаговый процесс декодирования")

                        steps = decoder.get_decoding_steps(tokens)
                        df = pd.DataFrame(steps)
                        df.columns = ["Шаг", "Токен", "Действие", "Добавлено", "Результат"]
                        st.dataframe(df, use_container_width=True, hide_index=True)

                except Exception as e:
                    st.error(f"Ошибка при декодировании: {str(e)}")

    st.markdown("---")
    st.caption("Приложение для кодирования и декодирования по методу LZ77")


if __name__ == "__main__":
    main()