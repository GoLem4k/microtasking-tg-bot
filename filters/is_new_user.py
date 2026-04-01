from db.services.users_service import UserService

user_service = UserService()


async def is_new_user(
    user_id: int,
    username: str | None,
    ref_parent_id: int | None = None,
) -> bool:
    user = await user_service.get_by_id(user_id)

    if user is None:
        await user_service.create(
            user_id=user_id,
            username=username,
            ref_parent_id=ref_parent_id,
        )

        if ref_parent_id is not None:
            await user_service.increment_referral_counters_for_new_user(user_id)

        print(
            f"[DEBUG] Это новый пользователь, добавлен в БД: id={user_id}, "
            f"ref_parent_id={ref_parent_id}"
        )
        return True

    if user.username != username:
        await user_service.update_username(
            user_id=user_id,
            username=username,
        )
        print(f"[DEBUG] Username обновлён для пользователя id={user_id}")

    print(f"[DEBUG] Это не новый пользователь: id={user_id}")
    return False
