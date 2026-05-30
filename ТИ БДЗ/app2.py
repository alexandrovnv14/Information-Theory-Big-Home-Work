"""
RSA Encryption/Decryption Protocol
Веб-приложение для шифрования и дешифрования по протоколу RSA
"""

import math
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional

import pandas as pd
import streamlit as st


@dataclass
class RSAKeyPair:
    """Пара ключей RSA"""
    p: int
    q: int
    n: int
    euler_n: int
    e: int
    d: int

    def public_key(self) -> Tuple[int, int]:
        return self.e, self.n

    def private_key(self) -> Tuple[int, int]:
        return self.d, self.n


class RSAUtils:
    """Вспомогательные математические функции для RSA"""

    @staticmethod
    def is_prime(n: int) -> bool:
        if n < 2:
            return False
        if n < 4:
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0:
                return False
            i += 6
        return True

    @staticmethod
    def gcd(a: int, b: int) -> int:
        while b:
            a, b = b, a % b
        return a

    @staticmethod
    def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
        """
        Расширенный алгоритм Евклида.
        Возвращает (gcd, x, y), где a*x + b*y = gcd(a, b)
        """
        if a == 0:
            return b, 0, 1

        gcd_val, x1, y1 = RSAUtils.extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1

        return gcd_val, x, y

    @staticmethod
    def extended_gcd_steps(a: int, b: int) -> List[dict]:
        """Расширенный алгоритм Евклида с записью шагов"""
        steps = []
        original_a, original_b = a, b

        while b != 0:
            q = a // b
            r = a % b
            steps.append({
                "a": a,
                "b": b,
                "q (частное)": q,
                "r (остаток)": r,
                "выражение": f"{a} = {b} * {q} + {r}"
            })
            a, b = b, r

        return steps

    @staticmethod
    def mod_inverse(e: int, phi: int) -> int:
        """Нахождение мультипликативного обратного: d = e^(-1) mod phi"""
        gcd_val, x, _ = RSAUtils.extended_gcd(e, phi)
        if gcd_val != 1:
            raise ValueError(f"Обратный элемент не существует: НОД({e}, {phi}) = {gcd_val}")
        return x % phi

    @staticmethod
    def mod_pow(base: int, exp: int, mod: int) -> int:
        """Быстрое возведение в степень по модулю"""
        result = 1
        base = base % mod
        while exp > 0:
            if exp % 2 == 1:
                result = (result * base) % mod
            exp = exp >> 1
            base = (base * base) % mod
        return result

    @staticmethod
    def mod_pow_steps(base: int, exp: int, mod: int) -> List[dict]:
        """Быстрое возведение в степень по модулю с записью шагов"""
        steps = []
        result = 1
        current_base = base % mod
        current_exp = exp
        step_num = 1

        while current_exp > 0:
            bit = current_exp % 2
            if bit == 1:
                old_result = result
                result = (result * current_base) % mod
                steps.append({
                    "шаг": step_num,
                    "бит экспоненты": bit,
                    "основание": current_base,
                    "действие": f"{old_result} * {current_base} mod {mod} = {result}",
                    "результат": result
                })
            else:
                steps.append({
                    "шаг": step_num,
                    "бит экспоненты": bit,
                    "основание": current_base,
                    "действие": "пропуск (бит = 0)",
                    "результат": result
                })

            current_exp = current_exp >> 1
            current_base = (current_base * current_base) % mod
            step_num += 1

        return steps

    @staticmethod
    def generate_prime(min_val: int = 100, max_val: int = 1000) -> int:
        """Генерация случайного простого числа в заданном диапазоне"""
        primes = [n for n in range(min_val, max_val + 1) if RSAUtils.is_prime(n)]
        if not primes:
            raise ValueError(f"Нет простых чисел в диапазоне [{min_val}, {max_val}]")
        return random.choice(primes)

    @staticmethod
    def find_public_exponent(phi: int) -> int:
        """Нахождение открытой экспоненты e: 1 < e < phi, НОД(e, phi) = 1"""
        # Стандартные значения e
        for e in [65537, 257, 17, 13, 11, 7, 5, 3]:
            if e < phi and RSAUtils.gcd(e, phi) == 1:
                return e

        # Поиск подходящего e
        for e in range(3, phi, 2):
            if RSAUtils.gcd(e, phi) == 1:
                return e

        raise ValueError("Не удалось найти подходящую открытую экспоненту")

    @staticmethod
    def get_all_valid_e(phi: int, max_count: int = 50) -> List[int]:
        """Получение списка допустимых значений e"""
        valid = []
        for e in range(2, phi):
            if RSAUtils.gcd(e, phi) == 1:
                valid.append(e)
                if len(valid) >= max_count:
                    break
        return valid


class RSACipher:
    """Шифрование и дешифрование RSA"""

    def __init__(self):
        self.utils = RSAUtils()

    def generate_keys(self, p: int, q: int, e: Optional[int] = None) -> RSAKeyPair:
        """Генерация ключей RSA на основе двух простых чисел"""
        if not RSAUtils.is_prime(p):
            raise ValueError(f"{p} не является простым числом")
        if not RSAUtils.is_prime(q):
            raise ValueError(f"{q} не является простым числом")
        if p == q:
            raise ValueError("Числа p и q должны различаться")

        n = p * q
        euler_n = (p - 1) * (q - 1)

        if e is None:
            e = RSAUtils.find_public_exponent(euler_n)
        else:
            if e <= 1 or e >= euler_n:
                raise ValueError(f"e должно удовлетворять условию: 1 < e < {euler_n}")
            if RSAUtils.gcd(e, euler_n) != 1:
                raise ValueError(f"НОД({e}, {euler_n}) != 1. Выберите другое значение e")

        d = RSAUtils.mod_inverse(e, euler_n)

        return RSAKeyPair(p=p, q=q, n=n, euler_n=euler_n, e=e, d=d)

    def encrypt_number(self, m: int, e: int, n: int) -> int:
        """Шифрование числа: c = m^e mod n"""
        if m < 0 or m >= n:
            raise ValueError(f"Сообщение m должно быть в диапазоне [0, {n - 1}]")
        return RSAUtils.mod_pow(m, e, n)

    def decrypt_number(self, c: int, d: int, n: int) -> int:
        """Дешифрование числа: m = c^d mod n"""
        return RSAUtils.mod_pow(c, d, n)

    def encrypt_text(self, text: str, e: int, n: int) -> List[int]:
        """Шифрование текста посимвольно"""
        encrypted = []
        for char in text:
            m = ord(char)
            if m >= n:
                raise ValueError(
                    f"Код символа '{char}' ({m}) >= n ({n}). "
                    f"Увеличьте значения p и q"
                )
            c = self.encrypt_number(m, e, n)
            encrypted.append(c)
        return encrypted

    def decrypt_text(self, encrypted: List[int], d: int, n: int) -> str:
        """Дешифрование текста"""
        decrypted = []
        for c in encrypted:
            m = self.decrypt_number(c, d, n)
            decrypted.append(chr(m))
        return "".join(decrypted)

    def get_encryption_steps(self, text: str, e: int, n: int) -> List[dict]:
        """Пошаговое шифрование"""
        steps = []
        for i, char in enumerate(text):
            m = ord(char)
            c = self.encrypt_number(m, e, n)
            steps.append({
                "шаг": i + 1,
                "символ": repr(char),
                "код символа (m)": m,
                "вычисление": f"{m}^{e} mod {n}",
                "шифротекст (c)": c
            })
        return steps

    def get_decryption_steps(self, encrypted: List[int], d: int, n: int) -> List[dict]:
        """Пошаговое дешифрование"""
        steps = []
        for i, c in enumerate(encrypted):
            m = self.decrypt_number(c, d, n)
            char = chr(m)
            steps.append({
                "шаг": i + 1,
                "шифротекст (c)": c,
                "вычисление": f"{c}^{d} mod {n}",
                "код символа (m)": m,
                "символ": repr(char)
            })
        return steps


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
            .key-box {
                padding: 10px 14px;
                border: 1px solid #cccccc;
                border-radius: 6px;
                background-color: #f9f9f9;
                margin-bottom: 0.5rem;
                font-family: monospace;
            }
        </style>
    """, unsafe_allow_html=True)


def parse_encrypted_input(text: str) -> List[int]:
    """Парсинг зашифрованных чисел из строки"""
    text = text.strip()
    if not text:
        return []

    parts = text.replace(",", " ").split()
    numbers = []
    for part in parts:
        part = part.strip()
        if part:
            numbers.append(int(part))
    return numbers


def main():
    st.set_page_config(
        page_title="RSA: шифрование и дешифрование",
        layout="wide"
    )

    apply_styles()

    st.title("RSA: протокол шифрования и дешифрования")

    st.markdown("""
    <div class="app-note">
        Алгоритм RSA — асимметричный криптографический алгоритм, основанный
        на вычислительной сложности задачи факторизации больших целых чисел.
        <br><br>
        <b>Открытый ключ:</b> (e, n) — используется для шифрования.<br>
        <b>Закрытый ключ:</b> (d, n) — используется для дешифрования.<br><br>
        <b>Шифрование:</b> c = m<sup>e</sup> mod n<br>
        <b>Дешифрование:</b> m = c<sup>d</sup> mod n
    </div>
    """, unsafe_allow_html=True)

    cipher = RSACipher()

    tab1, tab2, tab3 = st.tabs(["Генерация ключей", "Шифрование", "Дешифрование"])

    # --- Генерация ключей ---
    with tab1:
        st.header("Генерация ключей RSA")

        col_input, col_space, col_result = st.columns([2, 0.5, 3])

        with col_input:
            st.subheader("Входные параметры")

            p = st.number_input("Простое число p", min_value=2, value=61, step=1, key="key_p")
            q = st.number_input("Простое число q", min_value=2, value=53, step=1, key="key_q")

            auto_e = st.checkbox("Выбрать e автоматически", value=True, key="auto_e")

            custom_e = None
            if not auto_e:
                custom_e = st.number_input(
                    "Открытая экспонента e",
                    min_value=2,
                    value=17,
                    step=1,
                    key="custom_e"
                )

            generate_button = st.button("Сгенерировать ключи", type="primary", key="gen_btn")

            st.markdown("---")

            if st.button("Случайные p и q", key="random_btn"):
                rand_p = RSAUtils.generate_prime(100, 500)
                rand_q = RSAUtils.generate_prime(100, 500)
                while rand_q == rand_p:
                    rand_q = RSAUtils.generate_prime(100, 500)
                st.info(f"Сгенерированы: p = {rand_p}, q = {rand_q}. Введите их в поля выше.")

        with col_result:
            if generate_button:
                try:
                    keys = cipher.generate_keys(int(p), int(q), int(custom_e) if custom_e else None)

                    st.subheader("Результаты генерации")

                    st.markdown("**Промежуточные вычисления**")

                    calc_steps = [
                        {"параметр": "p", "значение": keys.p, "описание": "первое простое число"},
                        {"параметр": "q", "значение": keys.q, "описание": "второе простое число"},
                        {"параметр": "n = p * q", "значение": keys.n,
                         "описание": f"{keys.p} * {keys.q} = {keys.n}"},
                        {"параметр": "phi(n) = (p-1)(q-1)", "значение": keys.euler_n,
                         "описание": f"({keys.p}-1) * ({keys.q}-1) = {keys.euler_n}"},
                        {"параметр": "e", "значение": keys.e,
                         "описание": f"НОД({keys.e}, {keys.euler_n}) = 1"},
                        {"параметр": "d = e^(-1) mod phi(n)", "значение": keys.d,
                         "описание": f"{keys.e} * {keys.d} mod {keys.euler_n} = "
                                     f"{(keys.e * keys.d) % keys.euler_n}"},
                    ]

                    df_calc = pd.DataFrame(calc_steps)
                    df_calc.columns = ["Параметр", "Значение", "Описание"]
                    st.dataframe(df_calc, use_container_width=True, hide_index=True)

                    col_pub, col_priv = st.columns(2)

                    with col_pub:
                        st.markdown("**Открытый ключ**")
                        st.markdown(f'<div class="key-box">e = {keys.e}<br>n = {keys.n}</div>',
                                    unsafe_allow_html=True)

                    with col_priv:
                        st.markdown("**Закрытый ключ**")
                        st.markdown(f'<div class="key-box">d = {keys.d}<br>n = {keys.n}</div>',
                                    unsafe_allow_html=True)

                    # Проверка
                    st.markdown("**Проверка корректности ключей**")
                    test_m = 42 if 42 < keys.n else 2
                    test_c = cipher.encrypt_number(test_m, keys.e, keys.n)
                    test_d = cipher.decrypt_number(test_c, keys.d, keys.n)

                    verification = [
                        {"действие": "Исходное число", "результат": test_m},
                        {"действие": f"Шифрование: {test_m}^{keys.e} mod {keys.n}",
                         "результат": test_c},
                        {"действие": f"Дешифрование: {test_c}^{keys.d} mod {keys.n}",
                         "результат": test_d},
                        {"действие": "Совпадение",
                         "результат": "Да" if test_m == test_d else "Нет"},
                    ]
                    df_ver = pd.DataFrame(verification)
                    df_ver.columns = ["Действие", "Результат"]
                    st.dataframe(df_ver, use_container_width=True, hide_index=True)

                    # Расширенный алгоритм Евклида
                    st.markdown("**Расширенный алгоритм Евклида для нахождения d**")
                    gcd_steps = RSAUtils.extended_gcd_steps(keys.e, keys.euler_n)
                    if gcd_steps:
                        df_gcd = pd.DataFrame(gcd_steps)
                        st.dataframe(df_gcd, use_container_width=True, hide_index=True)

                    # Допустимые значения e
                    valid_e_list = RSAUtils.get_all_valid_e(keys.euler_n, max_count=30)
                    st.markdown(
                        f"**Допустимые значения e** (первые {len(valid_e_list)} из возможных)"
                    )
                    st.code(", ".join(str(x) for x in valid_e_list), language=None)

                    # Сохраняем ключи в session_state
                    st.session_state["rsa_keys"] = keys

                except Exception as ex:
                    st.error(f"Ошибка генерации ключей: {str(ex)}")

    # --- Шифрование ---
    with tab2:
        st.header("Шифрование")

        col_in, col_sp, col_out = st.columns([2, 0.5, 3])

        with col_in:
            st.subheader("Параметры шифрования")

            # Автозаполнение из сгенерированных ключей
            default_e = 17
            default_n = 3233
            if "rsa_keys" in st.session_state:
                default_e = st.session_state["rsa_keys"].e
                default_n = st.session_state["rsa_keys"].n

            enc_e = st.number_input(
                "Открытая экспонента e",
                min_value=2, value=default_e, step=1, key="enc_e"
            )
            enc_n = st.number_input(
                "Модуль n",
                min_value=2, value=default_n, step=1, key="enc_n"
            )

            enc_mode = st.radio(
                "Режим ввода",
                ["Текст", "Число"],
                horizontal=True,
                key="enc_mode"
            )

            if enc_mode == "Текст":
                enc_input = st.text_area(
                    "Введите текст для шифрования",
                    value="HELLO",
                    height=100,
                    key="enc_text"
                )
            else:
                enc_input = st.number_input(
                    "Введите число для шифрования",
                    min_value=0, value=65, step=1, key="enc_num"
                )

            encrypt_button = st.button("Зашифровать", type="primary", key="enc_btn")

        with col_out:
            if encrypt_button:
                try:
                    e_val = int(enc_e)
                    n_val = int(enc_n)

                    if enc_mode == "Текст":
                        encrypted = cipher.encrypt_text(str(enc_input), e_val, n_val)

                        st.subheader("Результат шифрования")

                        encrypted_str = " ".join(str(c) for c in encrypted)
                        st.code(encrypted_str, language=None)
                        st.text_input(
                            "Шифротекст для копирования",
                            value=encrypted_str,
                            key="enc_result"
                        )

                        st.subheader("Пошаговый процесс шифрования")
                        steps = cipher.get_encryption_steps(str(enc_input), e_val, n_val)
                        df_enc = pd.DataFrame(steps)
                        st.dataframe(df_enc, use_container_width=True, hide_index=True)

                    else:
                        m_val = int(enc_input)
                        c_val = cipher.encrypt_number(m_val, e_val, n_val)

                        st.subheader("Результат шифрования")
                        st.code(f"c = {m_val}^{e_val} mod {n_val} = {c_val}", language=None)

                        st.subheader("Быстрое возведение в степень")
                        pow_steps = RSAUtils.mod_pow_steps(m_val, e_val, n_val)
                        if pow_steps:
                            df_pow = pd.DataFrame(pow_steps)
                            st.dataframe(df_pow, use_container_width=True, hide_index=True)

                except Exception as ex:
                    st.error(f"Ошибка шифрования: {str(ex)}")

    # --- Дешифрование ---
    with tab3:
        st.header("Дешифрование")

        col_in2, col_sp2, col_out2 = st.columns([2, 0.5, 3])

        with col_in2:
            st.subheader("Параметры дешифрования")

            default_d = 2753
            default_n2 = 3233
            if "rsa_keys" in st.session_state:
                default_d = st.session_state["rsa_keys"].d
                default_n2 = st.session_state["rsa_keys"].n

            dec_d = st.number_input(
                "Закрытая экспонента d",
                min_value=2, value=default_d, step=1, key="dec_d"
            )
            dec_n = st.number_input(
                "Модуль n",
                min_value=2, value=default_n2, step=1, key="dec_n"
            )

            dec_mode = st.radio(
                "Режим ввода",
                ["Последовательность чисел", "Одно число"],
                horizontal=True,
                key="dec_mode"
            )

            if dec_mode == "Последовательность чисел":
                dec_input = st.text_area(
                    "Введите зашифрованные числа (через пробел или запятую)",
                    value="",
                    height=100,
                    help="Например: 2790 1743 131 131 2527",
                    key="dec_text"
                )
            else:
                dec_input = st.number_input(
                    "Введите зашифрованное число",
                    min_value=0, value=2790, step=1, key="dec_num"
                )

            decrypt_button = st.button("Дешифровать", type="primary", key="dec_btn")

        with col_out2:
            if decrypt_button:
                try:
                    d_val = int(dec_d)
                    n_val = int(dec_n)

                    if dec_mode == "Последовательность чисел":
                        encrypted_numbers = parse_encrypted_input(str(dec_input))

                        if not encrypted_numbers:
                            st.warning("Введите хотя бы одно число.")
                        else:
                            decrypted_text = cipher.decrypt_text(encrypted_numbers, d_val, n_val)

                            st.subheader("Результат дешифрования")
                            st.code(decrypted_text, language=None)
                            st.text_input(
                                "Дешифрованный текст для копирования",
                                value=decrypted_text,
                                key="dec_result"
                            )

                            st.subheader("Пошаговый процесс дешифрования")
                            steps = cipher.get_decryption_steps(
                                encrypted_numbers, d_val, n_val
                            )
                            df_dec = pd.DataFrame(steps)
                            st.dataframe(df_dec, use_container_width=True, hide_index=True)

                    else:
                        c_val = int(dec_input)
                        m_val = cipher.decrypt_number(c_val, d_val, n_val)

                        st.subheader("Результат дешифрования")
                        st.code(
                            f"m = {c_val}^{d_val} mod {n_val} = {m_val}  "
                            f"(символ: {repr(chr(m_val))})",
                            language=None
                        )

                        st.subheader("Быстрое возведение в степень")
                        pow_steps = RSAUtils.mod_pow_steps(c_val, d_val, n_val)
                        if pow_steps:
                            df_pow = pd.DataFrame(pow_steps)
                            st.dataframe(df_pow, use_container_width=True, hide_index=True)

                except Exception as ex:
                    st.error(f"Ошибка дешифрования: {str(ex)}")

    st.markdown("---")
    st.caption("Приложение для шифрования и дешифрования по протоколу RSA")


if __name__ == "__main__":
    main()