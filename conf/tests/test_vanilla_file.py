from apps.vanilla_file_to_experiment import ThisIsAClass

def test_vanilla():
  thing = ThisIsAClass()
  assert "frank hello" == thing.this_is_a_method('frank ')


