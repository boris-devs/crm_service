from aiogram import F, Router, html
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.modules.leads.schemas import BotApplication
from app.modules.leads.service import LeadService
from app.telegram import keyboards
from app.telegram.utils import sender_from

class ApplicationForm(StatesGroup):
    name = State()
    contact = State()
    service = State()
    request = State()


async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ApplicationForm.name)
    await message.answer(
        "Здравствуйте! Я соберу заявку для нашего агентства — это займёт минуту.\n\n"
        "Как к вам обращаться?",
        reply_markup=keyboards.name_keyboard(message.from_user.full_name),
    )


async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Заявка отменена.", reply_markup=keyboards.restart_keyboard())


async def take_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip()[:255])
    await state.set_state(ApplicationForm.contact)
    await message.answer(
        "Как с вами связаться? Отправьте номер кнопкой ниже, напишите телефон/email "
        "или выберите связь в Telegram.",
        reply_markup=keyboards.contact_keyboard(),
    )


async def take_phone(message: Message, state: FSMContext, services: list[str]) -> None:
    await _ask_service(message, state, services, contact=message.contact.phone_number)


async def take_contact(message: Message, state: FSMContext, services: list[str]) -> None:
    contact = None if message.text == keyboards.USE_TELEGRAM else message.text.strip()[:255]
    await _ask_service(message, state, services, contact=contact)


async def _ask_service(message: Message, state: FSMContext, services: list[str], contact: str | None) -> None:
    await state.update_data(contact=contact)
    await state.set_state(ApplicationForm.service)
    await message.answer("Контакт сохранён ✅", reply_markup=ReplyKeyboardRemove())
    await message.answer("Какая услуга вас интересует?", reply_markup=keyboards.services_keyboard(services))


async def take_service(
    callback: CallbackQuery,
    callback_data: keyboards.ServiceCallback,
    state: FSMContext,
    services: list[str],
) -> None:
    if not 0 <= callback_data.index < len(services):
        await callback.answer("Эта кнопка устарела", show_alert=True)
        return
    service = services[callback_data.index]
    await state.update_data(service=service)
    await state.set_state(ApplicationForm.request)
    await callback.message.edit_text(f"Услуга: {html.bold(html.quote(service))}")
    await callback.message.answer("Опишите задачу в паре предложений: что нужно сделать, сроки, бюджет.")
    await callback.answer()


async def take_request(message: Message, state: FSMContext, lead_service: LeadService) -> None:
    data = await state.get_data()
    await state.clear()
    lead = await lead_service.create_from_bot(
        BotApplication(
            name=data["name"],
            contact=data.get("contact"),
            service=data.get("service"),
            request=message.text.strip(),
            sender=sender_from(message.from_user),
        )
    )
    await message.answer(
        f"Спасибо! Заявка {html.bold(f'№{lead.id}')} принята — менеджер свяжется с вами в ближайшее время.",
        reply_markup=keyboards.restart_keyboard(),
    )


async def unexpected_input(message: Message) -> None:
    await message.answer("Пожалуйста, ответьте текстом или используйте кнопки. Отменить: /cancel")


async def fallback(message: Message) -> None:
    await message.answer(
        "Чтобы оставить заявку, нажмите кнопку ниже или отправьте /start",
        reply_markup=keyboards.restart_keyboard(),
    )


def create_router() -> Router:
    router = Router(name="application")
    router.message.register(start, CommandStart())
    router.message.register(start, F.text == keyboards.NEW_APPLICATION)
    router.message.register(cancel, Command("cancel"), StateFilter("*"))
    router.message.register(take_name, ApplicationForm.name, F.text)
    router.message.register(take_phone, ApplicationForm.contact, F.contact)
    router.message.register(take_contact, ApplicationForm.contact, F.text)
    router.callback_query.register(take_service, ApplicationForm.service, keyboards.ServiceCallback.filter())
    router.message.register(take_request, ApplicationForm.request, F.text)
    router.message.register(unexpected_input, StateFilter(ApplicationForm))
    router.message.register(fallback)
    return router
