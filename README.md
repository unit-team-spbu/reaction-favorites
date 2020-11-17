# Сервис избранных мероприятий

Данный документ содержит описание работы и информацию о развертке микросервиса, предназначенного для хранения информации о мероприятиях, добавленных пользователем в избранное и отправляющего информацию о добавлениях в сервис интересов пользователей.

Название: `favorites`

Структура сервиса:

| Файл                 | Описание                                                          |
| -------------------- | ----------------------------------------------------------------- |
| `favorites.py`       | Код микросервиса                                                  |
| `config.yml`         | Конфигурационный файл со строкой подключения к RabbitMQ и MongoDB |
| `run.sh`             | Файл для запуска краулера из Docker контейнера                    |
| `requirements.txt`   | Верхнеуровневые зависимости                                       |
| `Dockerfile`         | Описание сборки контейнера сервиса                                |
| `docker-compose.yml` | Изолированная развертка сервиса вместе с (RabbitMQ, MongoDB)      |
| `README.md`          | Описание микросервиса                                             |

## API

### RPC

Добавление в избранное:

```bat
n.rpc.favorites.new_fav(fav_data)

Args: fav_data = [user_id, event_id]
Returns: nothing
Dispatch to the `uis`: [user_id, event_id]
```

Исключение из избранного:

```bat
n.rpc.favorites.cancel_fav(fav_data)

Args: fav_data = [user_id, event_id]
Returns: nothing
Dispatch to the `uis`: [user_id, event_id]
```

Получить список ид мероприятий, которые пользователь добавил в избранное:

```bat
n.rpc.favorites.get_favs_by_id(user_id)

Args: user_id
Returns: [event_1_id, ..., event_n_id]
```

Узнать, добавил ли пользователь данное мероприятие в избранное:

```bat
n.rpc.favorites.is_event_faved(user_id, event_id)

Args: user_id, event_id
Returns: True is event is faved, False otherwise
```

### HTTP

Добавление в избранное:

```rst
POST http://localhost:8000/new_fav HTTP/1.1
Content-Type: application/json

[user_id, event_id]
```

Исключение из избранного:

```rst
POST http://localhost:8000/cancel_fav HTTP/1.1
Content-Type: application/json

[user_id, event_id]
```

Получить список ид мероприятий, которые пользователь добавил в избранное:

```rst
GET http://localhost:8000/get_favs/<id> HTTP/1.1
```

Узнать, добавил ли пользователь данное мероприятие в избранное:

```rst
GET http://localhost:8000/is_faved/<user_id>/<event_id> HTTP/1.1
```

## Развертывание и запуск

### Локальный запуск

Для локального запуска микросервиса требуется запустить контейнер с RabbitMQ и MongoDB.

```bat
docker-compose up -d
```

Затем из папки микросервиса вызвать

```bat
nameko run favorites
```

Для проверки `rpc` запустите в командной строке:

```bat
nameko shell
```

После чего откроется интерактивная Python среда. Обратитесь к сервису одной из команд, представленных выше в разделе `rpc`.

### Запуск в контейнере

Чтобы запустить микросервис в контейнере вызовите команду:

```bat
docker-compose up
```

> если вы не хотите просмотривать логи, добавьте флаг `-d` в конце

Микросервис запустится вместе с RabbitMQ и MongoDB в контейнерах.

> Во всех случаях запуска вместе с MongoDB также разворачивается mongo-express - инструмент, с помощью которого можно просматривать и изменять содержимое подключенной базы (подключение в контейнерах сконфигурировано и производится автоматически). Сервис хостится локально на порту 8081.
