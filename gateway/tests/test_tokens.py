from gateway.tokens import Tokens


def test_generate_saves_tokens(tokens):
    token_uuid1 = tokens.generate('uuid1')
    token_uuid2 = tokens.generate('uuid2')
    token_uuid3 = tokens.generate('uuid3')

    tokens2 = Tokens(tokens.path)
    assert tokens2.exists('uuid1')
    assert tokens2.get('uuid1') == token_uuid1
    assert tokens2.exists('uuid2')
    assert tokens2.get('uuid2') == token_uuid2
    assert tokens2.exists('uuid3')
    assert tokens2.get('uuid3') == token_uuid3


def test_generate_overwrites(tokens):
    first_token_uuid1 = tokens.generate('uuid1')
    second_token_uuid1 = tokens.generate('uuid1')

    assert tokens.get('uuid1') != first_token_uuid1
    assert tokens.get('uuid1') == second_token_uuid1
