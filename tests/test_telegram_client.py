import pytest
from abp_tutor.telegram_client import _split_message, escape_markdown_v2

def test_escape_markdown_v2():
    # Testa os caracteres que precisam de escape no V2: _ * [ ] ( ) ~ ` > # + - = | { } . !
    original = "Hello! Check this: https://example.com/ (it's cool-ish) [test]"
    escaped = escape_markdown_v2(original)
    
    assert r"\!" in escaped
    assert r"\:" not in escaped # : is not escaped
    assert r"\(" in escaped
    assert r"\-" in escaped
    assert r"\[" in escaped
    
    # Não deve fazer double escape
    already_escaped = r"Hello\!"
    escaped2 = escape_markdown_v2(already_escaped)
    assert escaped2 == r"Hello\!"

def test_split_message_short():
    msg = "Mensagem curta."
    chunks = _split_message(msg)
    assert len(chunks) == 1
    assert chunks[0] == msg

def test_split_message_long():
    # Cria um texto com mais de 4096 caracteres, separado por parágrafos
    p1 = "A" * 2000
    p2 = "B" * 2000
    p3 = "C" * 1000
    msg = f"{p1}\n\n{p2}\n\n{p3}"
    
    chunks = _split_message(msg)
    
    # 2000 + 2000 + 2 = 4002 (cabe na primeira)
    # 1000 (vai para a segunda)
    assert len(chunks) == 2
    assert chunks[0] == f"{p1}\n\n{p2}"
    assert chunks[1] == p3
