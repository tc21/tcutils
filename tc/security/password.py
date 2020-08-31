import secrets
import string


def auto_generate_password(style='apple', length=None):
    if style in builtin_styles:
        proposed_length, get_set = builtin_styles[style]
    else:
        raise ValueError(f"unknown style '{style}'")

    if length is None:
        length = proposed_length

    return generate_password(length, get_set)


def roll_one_in_n(n: int) -> bool:
    return secrets.randbelow(n) == 0


def apple_get_set(length: int, up_until_now: str) -> str:
    default_set = 'bcdfghjklmnpqrstvwxz'
    uppercase_set = 'BCDFGHJKLMNPQRSTVWXZ'
    vowels_set = 'aeiouy'
    uppercase_vowels_set = 'AEIOUY'
    digits_set = '0123456789'

    if length is not None and length != 20:
        raise ValueError('invalid length: do not provide a length')

    if len(up_until_now) in (6, 13):
        return '-'

    if len(up_until_now) == 20:
        return None

    remaining_chars = 18 - len(up_until_now.replace('-', ''))
    digit_used = any(x in up_until_now for x in digits_set)
    uppercase_used = any(x.isupper() for x in up_until_now)

    digit_positions = [0, 5, 7, 12, 14, 19]
    if not digit_used and len(up_until_now) in digit_positions:
        reminaing_digit_chars = len(digit_positions) - digit_positions.index(len(up_until_now))
        if roll_one_in_n(reminaing_digit_chars):
            return digits_set

    if not uppercase_used:
        if digit_used:
            uppercase = roll_one_in_n(remaining_chars)
        else:
            uppercase = roll_one_in_n(remaining_chars - 1)
    else:
        uppercase = False

    vowel_positions = [1, 4, 8, 11, 15, 18]
    if digit_used:
        digit_pos = [x in digits_set for x in up_until_now].index(True)
        if digit_pos in (0, 7, 14):
            x = digit_pos // 7 * 2
            vowel_positions[x] += 1
            vowel_positions[x+1] += 1

    if len(up_until_now) in vowel_positions:
        return uppercase_vowels_set if uppercase else vowels_set

    return uppercase_set if uppercase else default_set


def generate_password(length=18, get_set=string.ascii_lowercase):
    try:
        if callable(get_set):
            x = get_set(length, '')
        else:
            x = get_set
            if length is None:
                raise TypeError('length cannot be None when get_set is not a function')
        assert type(secrets.choice(x)) == str
    except (TypeError, AssertionError):
        raise TypeError('get_set must be a str or Callable[[int, str], str]')

    def get_character_set(total_length, up_until_now):
        if callable(get_set):
            return get_set(total_length, up_until_now)
        else:
            return get_set

    current_password = ''

    for _ in range(128):
        if len(current_password) == length:
            break

        next_character_set = get_character_set(length, current_password)
        if next_character_set is None:
            if length is None:
                break
            raise ValueError(f'failed to generate a password of len {length} (stopped after {len(current_password)} characters)!')

        current_password += secrets.choice(next_character_set)
    else:
        raise ValueError('get_set did not terminate after 128 characters; please provide a length')

    return current_password


def generate_static_password(
    effective_length=18, segment_separator='-', segment_length=6,
    default_set=string.ascii_lowercase, extra_sets=dict()
):
    '''
    `effective_length` number of effective (non-separator) characters in the
        generated password (actual length may be longer)\\
    `segment_separator` character used to separate segments\\
    `segment_length` length of segments\\
    `default_set: Iterable[str]` default allowed characters in the password;
        most of the password should be comprised from this set\\
    `extra_sets: Dict[Iterable[str], int]` `Iterable`-`int` pairs of
        non-default character sets and the number of characters to choose from
        that set
    '''
    current_length = 0
    extra_sets = {key: value for key, value in extra_sets.items() if value > 0}

    def remaining_length():
        return effective_length - current_length

    def should_select(extra_set):
        return secrets.randbelow(remaining_length()) < extra_sets[extra_set]

    def generate_character():
        selected_set = default_set

        # calculate if we should use a character from the extra sets
        random_value = secrets.randbelow(remaining_length())
        threshold = 0
        for s, i in extra_sets.items():
            threshold += i
            if random_value < threshold:
                selected_set = s

                extra_sets[s] -= 1
                if extra_sets[s] == 0:
                    del extra_sets[s]

                break

        nonlocal current_length
        current_length += 1

        return secrets.choice(selected_set)

    def generate_segment(length):
        return ''.join(generate_character() for _ in range(length))

    segments = []
    while segment_length < remaining_length():
        segments.append(generate_segment(segment_length))
    segments.append(generate_segment(remaining_length()))

    return segment_separator.join(segments)


builtin_styles = {
    'apple': (None, apple_get_set),
    'lastpass': (16, string.ascii_letters + string.digits + '!#$%&*@^')
}
