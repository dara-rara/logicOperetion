from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from requests import request
from service.bitwise_funcs import func_symbols
from service.forms import SessionForm
from service.model_level import build_model, generate_random_numbers, generate_level
from .models import Session
from datetime import datetime
import json
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages

class IndexView(View):
    def get(self, request):
        """Главная страница приложения"""
        return render(request, 'index.html')


class SessionStartView(View):
    def get(self, request):
        """Отображение формы для начала новой сессии"""
        form = SessionForm()
        return render(request, 'session_form.html', {'form': form})

    def post(self, request):
        """Обработка данных сессии"""
        form = SessionForm(request.POST)
        if form.is_valid():
            # Сохраняем данные в сессии
            request.session['user_name'] = form.cleaned_data['name']
            request.session['run_number'] = form.cleaned_data['run_number']
            request.session['start_time'] = timezone.now().isoformat()
            request.session['final_evaluation'] = True

            # Генерируем модель данных
            levels_data = build_model()
            request.session['levels_data'] = json.dumps(self.prepare_levels_data(levels_data))

            # Сохраняем сессию в БД
            session = Session.objects.create(
                user_name=form.cleaned_data['name'],
                run_number=form.cleaned_data['run_number'],
                start_time=timezone.now(),
                final_evaluation=request.session['final_evaluation'],
                levels_data=request.session['levels_data']
            )
            request.session['session_id'] = session.id

            return redirect('levels')

        return render(request, 'session_form.html', {'form': form})

    def prepare_levels_data(self, levels):
        """Преобразуем данные уровней для шаблона"""
        prepared_levels = []
        for level in levels:
            level_data = {
                'level': level['level'],
                'y_k': [],
                'l': level['l'],  # Добавляем количество элементов
                'data': []
            }

            if level['level'] == 0:
                # Для уровня 0 используем yk и k
                for yk, k in zip(level['yk'], level['k']):
                    level_data['data'].append({
                        'y': yk,
                        'k': k
                    })
                    level_data['y_k'].append(str(yk) + "_" + str(k))
            else:
                # Для остальных уровней
                for i in range(level['l']):
                    args_indices = level['args_ind'][i]

                    # Формируем аргументы
                    args_str = ", ".join([
                        f"{level['args_original'][idx]}_{level['args_bases'][idx]}"
                        for idx in args_indices
                    ])

                    # Формируем битовое представление
                    if len(args_indices) == 1:
                        bits_str = f"{level['args_binary'][args_indices[0]]}"
                    else:
                        bits_parts = [f"{level['args_binary'][idx]}" for idx in args_indices]
                        bits_str = f"({func_symbols[level['funcs'][i]]})".join(bits_parts)

                    level_data['data'].append({
                        'args': args_str,
                        'bits': bits_str,
                        'result': level['results'][i],
                        'base': level['k'][i]
                    })

            prepared_levels.append(level_data)

        # Помечаем последний уровень для ввода ответа
        if prepared_levels:
            prepared_levels[-1]['show_final_input'] = True

        return prepared_levels


class LevelsView(View):
    def get(self, request):
        """Отображение уровней с операциями"""
        # Проверка авторизации
        if 'user_name' not in request.session:
            messages.warning(request, 'Требуется авторизация')
            return redirect('session_start')

        try:
            # Загрузка данных уровней из сессии
            levels_data = json.loads(request.session.get('levels_data', '[]'))
        except (json.JSONDecodeError, TypeError) as e:
            messages.error(request, 'Ошибка загрузки данных уровней')
            print(f"Error loading levels data: {str(e)}")
            return redirect('session_start')

        # Подготовка данных для шаблона
        levels = self._prepare_levels_data(levels_data)
        context = {
            'user_name': request.session['user_name'],
            'run_number': request.session['run_number'],
            'levels': levels,
            'func_symbols': func_symbols,
        }
        return render(request, 'levels.html', context)

    def post(self, request):
        """Обработка финального ответа с учетом структуры данных в сессии"""
        try:
            if 'levels_data' not in request.session:
                return self._ajax_or_redirect(
                    request,
                    error='Сессия истекла',
                    redirect_url=reverse('session_start')
                )

            # Получение и валидация ответа
            user_answer = request.POST.get('final_answer', '').strip()
            if not user_answer:
                return self._ajax_or_redirect(
                    request,
                    error='Необходимо ввести ответ',
                    redirect_url=reverse('levels')
                )

            # Загрузка и проверка данных уровня
            levels_data = json.loads(request.session['levels_data'])
            if not levels_data:
                return self._ajax_or_redirect(
                    request,
                    error='Нет данных уровней',
                    redirect_url=reverse('session_start')
                )

            last_level = levels_data[-1]

            # Обработка ответа
            results = self._process_level_answers(user_answer, last_level)
            if not results:
                return self._ajax_or_redirect(
                    request,
                    error='Ошибка обработки ответа',
                    redirect_url=reverse('levels')
                )

            # Сохранение результатов
            self._save_session_results(request, results, user_answer, last_level)

            return self._ajax_or_redirect(
                request,
                success=True,
                redirect_url=reverse('results_view')
            )

        except Exception as e:
            print(f"Error in LevelsView.post: {str(e)}")
            return self._ajax_or_redirect(
                request,
                error='Ошибка обработки ответа',
                redirect_url=reverse('levels')
            )

    def _ajax_or_redirect(self, request, error=None, success=False, redirect_url=None):
        """Вспомогательный метод для обработки AJAX и обычных запросов"""
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Для AJAX-запросов возвращаем JSON
            return JsonResponse({
                'status': 'error' if error else 'success',
                'error': error,
                'redirect': success,
                'redirect_url': redirect_url
            }, status=400 if error else 200)
        else:
            # Для обычных запросов - редирект с сообщением
            if error:
                messages.error(request, error)
            return HttpResponseRedirect(redirect_url)

    def _process_level_answers(self, user_answer, level_data):
        """Обработка ответов для структуры данных уровня"""
        try:
            # Получаем эталонные ответы из данных уровня
            expected_answers = []
            for item in level_data.get('data', []):
                if 'result' in item and 'base' in item:
                    expected_answers.append({
                        'value': item['result'],
                        'base': item['base']
                    })

            if not expected_answers:
                messages.error(self.request, 'Нет данных для проверки ответов')
                return None

            # Парсинг ответов пользователя
            user_answers = []
            for answer in user_answer.split():
                try:
                    if '_' in answer:
                        num_str, base_str = answer.split('_', 1)
                        user_answers.append({
                            'value': int(num_str),
                            'base': int(base_str),
                            'str': answer
                        })
                    else:
                        user_answers.append({
                            'value': int(answer),
                            'base': 10,
                            'str': f"{answer}_10"
                        })
                except ValueError:
                    messages.error(self.request, f'Неверный формат ответа: {answer}')
                    return None

            # Проверка количества ответов
            if len(user_answers) != len(expected_answers):
                messages.error(self.request,
                               f'Ожидается {len(expected_answers)} ответов, получено {len(user_answers)}')
                return None

            # Проверка каждого ответа
            detailed_results = []
            correct_answer = []
            correct_count = 0

            for user_ans, expected in zip(user_answers, expected_answers):
                # Сравниваем числовые значения и основания
                is_correct = (user_ans['value'] == expected['value'] and
                              user_ans['base'] == expected['base'])

                if is_correct:
                    correct_count += 1

                correct_answer.append(f"{expected['value']}_{expected['base']}")
                detailed_results.append({
                    'user_answer': user_ans['str'],
                    'correct_answer': f"{expected['value']}_{expected['base']}",
                    'is_correct': is_correct,
                    'user_value': user_ans['value'],
                    'correct_value': expected['value'],
                    'base': expected['base']
                })

            return {
                'is_correct': correct_count == len(detailed_results),
                'total_count': len(detailed_results),
                'details': detailed_results,
                'correct_answer': correct_answer,
            }

        except Exception as e:
            messages.error(request, 'Ошибка проверки ответов')
            print(f"Answer processing error: {str(e)}")
            return None

    def _save_session_results(self, request, results, user_answer, level_data):
        """Сохранение результатов в сессию с дополнительной информацией"""
        if request.session['final_evaluation']:
            request.session['final_evaluation'] = results['is_correct']
        request.session['results'] = {
            'run_number': int(request.session['run_number']),
            'is_correct': results['is_correct'],
            'final_evaluation': request.session['final_evaluation'],
            'total_count': results['total_count'],
            'details': results['details'],
            'user_answer': user_answer,
            'correct_answer': " ".join(results['correct_answer']),
            'timestamp': datetime.now().isoformat(sep=' ', timespec='seconds'),
            'level_data': {  # Сохраняем ключевые данные уровня для отладки
                'level': level_data.get('level'),
                'operations_count': len(level_data.get('data', [])),
                'show_final_input': level_data.get('show_final_input', False)
            }
        }
        request.session.modified = True

    def _prepare_levels_data(self, levels_data):
        """Подготовка данных уровней для шаблона"""
        levels = []
        last_level_index = len(levels_data) - 1

        for i, level in enumerate(levels_data):
            level_data = {
                'level_num': level.get('level', 0),
                'is_last': last_level_index,
                'items': [],
                'y_k': level.get('y_k', 0)
            }

            for item in level.get('data', []):
                if level_data['level_num'] == 0:
                    level_data['items'].append({
                        'type': 'input',
                        'y': item.get('y', ''),
                        'k': item.get('k', '')
                    })
                else:
                    level_data['items'].append({
                        'type': 'operation',
                        'args': item.get('args', ''),
                        'bits': item.get('bits', ''),
                        'result': item.get('result'),
                        'base': item.get('base', '')
                    })
            levels.append(level_data)
        return levels


class ResultsView(View):
    def get(self, request):
        """Отображение результатов с гарантированным возвратом HttpResponse"""
        try:
            if 'results' not in request.session:
                messages.warning(request, 'Результаты не найдены')
                return HttpResponseRedirect(reverse('levels'))

            context = {
                'user_name': request.session.get('user_name', 'Гость'),
                'run_number': request.session.get('run_number', '0'),
                'results': request.session['results'],
                'percentage': self._calculate_percentage(request.session['results'])
            }
            return render(request, 'results.html', context)

        except Exception as e:
            messages.error(request, 'Ошибка загрузки результатов')
            print(f"Error in ResultsView.get: {str(e)}")
            return HttpResponseRedirect(reverse('levels'))

    def _calculate_percentage(self, results):
        """Вспомогательный метод с гарантированным возвратом значения"""
        try:
            correct = results.get('correct_count', 0)
            total = results.get('total_count', 1)  # избегаем деления на 0
            return int((correct / total) * 100)
        except:
            return 0


class ReferenceModelView(View):
    def get(self, request):
        try:
            # Загрузка данных уровней из сессии
            levels_data = json.loads(request.session.get('levels_data', '[]'))
        except (json.JSONDecodeError, TypeError) as e:
            messages.error(request, 'Ошибка загрузки данных уровней')
            print(f"Error loading levels data: {str(e)}")
            return redirect('session_start')
        context = {'levels': LevelsView()._prepare_levels_data(levels_data)}
        return render(request, 'reference_model.html', context)


def download_session_report(request):
    if 'results' not in request.session:
        return HttpResponse("Нет данных сессии", status=404)

    results = request.session['results']

    # Формируем структуру отчёта согласно заданию
    report_lines = [
        "ОТЧЁТ О ПРОВЕРКЕ МОДЕЛИ",
        "=" * 50,
        f"Дата: {results['timestamp']}",
        f"Пользователь: {request.session['user_name']}\n"
        f"Попытка: {request.session['run_number']}",
        "",
        "РЕЗУЛЬТАТЫ:",
        f"- Ответ пользователя: {results['user_answer']}",
        f"- Правильный ответ: {results['correct_answer']}",
        "",
        f"КОММЕНТАРИЙ ПОЛЬЗОВАТЕЛЯ:",
        results.get('user_comment', 'Нет комментария')
    ]

    # Создаём TXT-файл
    response = HttpResponse("\n".join(report_lines),
                            content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="model_test_report.txt"'
    return response

def save_comment(request):
    if request.method == 'POST' and 'results' in request.session:
        request.session['results']['user_comment'] = request.POST.get('user_comment', '')
        request.session.modified = True
        return render(request, 'results.html')
    return JsonResponse({'status': 'error'}, status=400)


class InstructionsView(View):
    def get(self, request):
        """Страница с инструкцией"""
        # Добавляем символы операций в контекст
        operation_symbols = [
            {'symbol': sym, 'name': name}
            for name, sym in func_symbols.items()
        ]

        context = {
            'operation_symbols': operation_symbols
        }
        return render(request, 'instructions.html', context)

def next_run(request):
    if 'run_number' in request.session:
        request.session['run_number'] = str(int(request.session['run_number']) + 1)
        # Генерируем модель данных
        levels_data = build_model()
        request.session['levels_data'] = json.dumps(SessionStartView().prepare_levels_data(levels_data))
        request.session.modified = True
    return redirect('levels')  # Перенаправляем на страницу тестирования

