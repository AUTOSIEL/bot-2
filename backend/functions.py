def get_functions():
    """
    Возвращает список инструментов (functions) в формате,
    совместимом с OpenAI Chat Completions API (model gpt-4o-mini и другие).
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "create_event",
                "description": "Создает одно или несколько событий или напоминаний в календаре пользователя.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reminders": {
                            "type": "array",
                            "description": "Список событий для создания.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "description": "Название события. Например, 'Встреча с командой'."},
                                    "start_date": {"type": "string", "description": "Дата и время начала в формате DD.MM.YYYY HH:MM."},
                                    "end_date": {"type": "string", "description": "Дата и время окончания в формате DD.MM.YYYY HH:MM. Может быть null."},
                                    "notify_before": {"type": "integer", "description": "За сколько МИНУТ до начала напомнить. Может быть null."},
                                    "notify_date": {"type": "string", "description": "Точная дата и время напоминания в формате DD.MM.YYYY HH:MM. Может быть null."},
                                    "event_type": {"type": "string", "enum": ["single", "recurring"], "description": "Тип события: 'single' для однократного, 'recurring' для повторяющегося."},
                                    "recurrence": {
                                        "type": "object",
                                        "description": "Правила повторения для 'recurring' событий. Для 'single' событий - null.",
                                        "properties": {
                                            "frequency": {"type": "string", "description": "Частота: 'daily', 'weekly', 'monthly', 'yearly'."},
                                            "interval": {"type": "integer", "description": "Интервал повторения, например, 2 для 'каждые 2 дня'."}
                                        }
                                    }
                                },
                                "required": ["title"]
                            }
                        }
                    },
                    "required": ["reminders"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "update_event",
                "description": "Обновляет одно или несколько существующих событий в календаре по их ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reminders": {
                            "type": "array",
                            "description": "Список событий для обновления.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer", "description": "Уникальный ID события, которое нужно обновить."},
                                    "title": {"type": "string"},
                                    "start_date": {"type": "string"},
                                    "end_date": {"type": "string", "description": "Может быть null."}
                                    # ... и другие поля, которые можно обновить
                                },
                                "required": ["id"]
                            }
                        }
                    },
                    "required": ["reminders"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "remove_event",
                "description": "Удаляет одно или несколько событий из календаря по их ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reminders": {
                            "type": "array",
                            "description": "Список событий для удаления.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer", "description": "Уникальный ID события, которое нужно удалить."}
                                },
                                "required": ["id"]
                            }
                        }
                    },
                    "required": ["reminders"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_note",
                "description": "Создает одну или несколько текстовых заметок.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "notes": {
                            "type": "array",
                            "description": "Список заметок для создания.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "description": "Заголовок заметки."},
                                    "content": {"type": "string", "description": "Содержимое заметки."}
                                },
                                "required": ["title", "content"]
                            }
                        }
                    },
                    "required": ["notes"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "update_note",
                "description": "Обновляет одну или несколько существующих заметок по их ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "notes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "title": {"type": "string"},
                                    "content": {"type": "string"}
                                },
                                "required": ["id"]
                            }
                        }
                    },
                    "required": ["notes"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "remove_note",
                "description": "Удаляет одну или несколько заметок по их ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "notes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"}
                                },
                                "required": ["id"]
                            }
                        }
                    },
                    "required": ["notes"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_task",
                "description": "Создает одну или несколько задач.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tasks": {
                            "type": "array",
                            "description": "Список задач для создания.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "description": "Название задачи."},
                                    "content": {"type": "string", "description": "Описание задачи. Может быть пустым."},
                                    "status": {"type": "integer", "description": "Статус задачи, обычно 0 для 'новой'."}
                                },
                                "required": ["title"]
                            }
                        }
                    },
                    "required": ["tasks"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "update_task",
                "description": "Обновляет одну или несколько существующих задач по их ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "title": {"type": "string"},
                                    "content": {"type": "string"},
                                    "status": {"type": "integer"}
                                },
                                "required": ["id"]
                            }
                        }
                    },
                    "required": ["tasks"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "remove_task",
                "description": "Удаляет одну или несколько задач по их ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"}
                                },
                                "required": ["id"]
                            }
                        }
                    },
                    "required": ["tasks"]
                }
            }
        }
    ]