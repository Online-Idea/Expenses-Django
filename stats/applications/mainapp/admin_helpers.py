def marks_mark(obj):
    return obj.mark.name


def models_model(obj):
    return obj.model.name


def generations_generation(obj):
    return obj.generation.generation


def complectations_complectation(obj):
    try:
        return obj.complectation.complectation
    except AttributeError:
        return ''


def modifications_modification(obj):
    return obj.modification.short_name


marks_mark.short_description = 'Марка'
models_model.short_description = 'Модель'
generations_generation.short_description = 'Поколение'
complectations_complectation.short_description = 'Комплектация'
modifications_modification.short_description = 'Модификация'
