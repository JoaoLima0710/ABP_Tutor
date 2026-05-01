import argparse
from datetime import date, timedelta
import sys

from abp_tutor import db_app, db_state, tutor, telegram_client, scheduler
from abp_tutor.config import get_settings
from abp_tutor.logging_setup import logger


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Gera o plano mas não salva nem envia")
    parser.add_argument("--resend", type=str, help="YYYY-MM-DD para reenviar um plano já salvo")
    args = parser.parse_args()

    settings = get_settings()
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Modo reenvio
    if args.resend:
        resend_date = date.fromisoformat(args.resend)
        plan = db_state.get_existing_plan(resend_date)
        if not plan:
            logger.error(f"Plano não encontrado para {resend_date}")
            return 1
            
        logger.info(f"Reenviando plano do dia {resend_date}")
        day_plan = {
            "day_index": plan["day_index"],
            "macro_topic": plan["macro_topic"],
            "subtopics": plan["subtopics"],
            "questions_target": plan["questions_target"],
            "flashcards_target": plan["flashcards_target"]
        }
        telegram_client.send_daily_package(resend_date, day_plan, plan)
        db_state.mark_delivered(plan["id"])
        return 0

    run_id = db_state.start_run(today) if not args.dry_run else None

    try:
        # 1. Resolve dia do cronograma
        day_plan = scheduler.get_day_for_date(today)
        if day_plan is None:
            logger.info("Hoje fora da janela de 30 dias. Encerrando.")
            if not args.dry_run:
                db_state.finish_run(run_id, "skipped")
            return 0

        # Idempotência
        existing = db_state.get_existing_plan(today)
        if existing and not args.dry_run:
            logger.info("Plano já existe para hoje. Apenas reenviando.")
            telegram_client.send_daily_package(today, day_plan, existing)
            db_state.mark_delivered(existing["id"])
            db_state.finish_run(run_id, "success", plan_date=today)
            return 0

        logger.info(f"Iniciando geração para dia {day_plan['day_index']}")

        # 2. Coleta dados de desempenho
        try:
            accuracy = db_app.get_accuracy_by_topic(yesterday - timedelta(days=6), yesterday)
            weak = db_app.get_weak_areas(yesterday - timedelta(days=6), yesterday, top_n=3)
            
            q_done = db_app.get_questions_done_yesterday(yesterday)
            fc_done = db_app.get_flashcards_done_yesterday(yesterday)
            compliance_yesterday = {
                "questions_done": q_done,
                "flashcards_done": fc_done,
                "text_read": True # Assumindo true para simplificar
            }
        except Exception as e:
            logger.warning(f"Falha ao ler dados do app, prosseguindo com zerados: {e}")
            accuracy, weak, compliance_yesterday = [], [], None

        # 2.5 Busca material de referência opcional
        ref_material = db_app.get_material_for_topic(day_plan["macro_topic"])

        # 3. Monta prompts
        system_prompt = scheduler.load_system_prompt()
        user_prompt = scheduler.render_user_prompt(
            day_plan=day_plan,
            today=today,
            exam_date=settings.EXAM_DATE,
            accuracy=accuracy,
            weak=weak,
            compliance_yesterday=compliance_yesterday,
            reference_material=ref_material,
        )

        # 4. Chama POE
        result = tutor.generate_daily_content(system_prompt, user_prompt)

        # 5. Persiste e Envia
        if args.dry_run:
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            plan_id = db_state.save_daily_plan(today, day_plan, result)
            telegram_client.send_daily_package(today, day_plan, result)
            db_state.mark_delivered(plan_id)
            db_state.finish_run(run_id, "success", plan_date=today)

        return 0

    except Exception as e:
        logger.exception("Falha no orquestrador")
        if not args.dry_run:
            db_state.finish_run(run_id, "error", error=str(e))
            try:
                telegram_client.send_alert(f"⚠️ Tutor ABP — Falha ao gerar conteúdo de hoje:\n{e}")
            except Exception:
                pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
