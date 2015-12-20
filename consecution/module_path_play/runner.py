from animals import cows
from animals import goats
import humans
import importlib

bull = cows.Bull()
calf = cows.Calf()
billy = goats.Billy()
nanny = goats.Nanny()
man = humans.Man()
man2 = humans.Man()


#print(str(bull.__class__))
#print(str(man.__class__))

#print(bull.__module__)

def get_obj_path(obj):
    try:
        module_name = obj.__module__
    except AttributeError:
        module_name = ''
    class_name = obj.__class__.__name__
    return '{} {}'.format(module_name, class_name).strip()

def get_object_for_import_string(import_string):
    words = import_string.split()
    if len(words) == 1:
        return eval(words[0])
    else:
        module_name, class_name = words
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

mystring = 'aaa'


for obj in [bull, calf, billy, nanny, man, man2, mystring]:
    path_string = get_obj_path(obj)
    print()
    print(repr(path_string))
    print(get_object_for_import_string(path_string))
    #print(get_obj_path(obj), get_obj_path(get_obj_path(obj)))

