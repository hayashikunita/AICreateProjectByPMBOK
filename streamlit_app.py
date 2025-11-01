from __future__ import annotations

import json
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from pmbok_gpt.generator import generate_text_document
from pmbok_gpt.config import AppSettings

st.set_page_config(page_title="AICreateProjectByPMBOK - Project JSON UI", layout="wide")

st.title("プロジェクト情報の作成（Streamlit UI）")

with st.sidebar:
    st.header("設定")
    level = st.radio(
        "収集レベル",
        options=["basic", "extended"],
        index=1,
        help="入力する項目の範囲を切り替えます。basic: 最小限 / extended: 会社標準の追加項目も入力"
    )
    default_out = "examples/project_from_ui.json" if level == "basic" else "examples/project_from_ui_ext.json"
    out_path = st.text_input(
        "保存先パス",
        value=default_out,
        help="画面の入力内容を保存するJSONファイルの相対/絶対パス。例: examples/project_from_ui.json"
    )
    st.caption("例: examples/project_from_ui.json")

    st.divider()
    st.header("実行設定（プロバイダ）")
    provider = st.radio(
        "プロバイダ",
        options=["stub", "openai", "azure"],
        index=0,
        help="stub: 疑似応答（課金なし・動作確認用）/ openai: OpenAI API / azure: Azure OpenAI"
    )
    model = st.text_input(
        "モデル/デプロイ名",
        value="gpt-4o-mini",
        help="OpenAI: モデル名（例 gpt-4o-mini）/ Azure: デプロイメント名"
    )
    temperature = st.slider(
        "temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.4,
        step=0.1,
        help="出力の創造性。低いほど厳密・高いほど多様（通常 0.2〜0.7）"
    )
    max_tokens = st.number_input(
        "max_tokens",
        value=1800,
        min_value=1,
        step=100,
        help="生成する最大トークン数（長文にするほど増やしてください）"
    )
    # 追加の挙動設定
    prefer_responses_api = st.checkbox(
        "Responses API を優先（OpenAIのみ）",
        value=False,
        help="Chat Completions ではなく Responses API を優先して呼び出します。gpt-5 系など新仕様モデルでの不具合回避に有効です。"
    )
    fallback_stub = st.checkbox(
        "空出力時にスタブへフォールバック",
        value=True,
        help="LLMが空の本文を返した場合でも空ファイルにしないための保険です。無効にすると空出力をエラーとして検出できます。"
    )
    if (model or "").lower().find("gpt-5") >= 0:
        st.caption("ヒント: gpt-5 系モデルでは Responses API 優先が推奨です。temperature は無視される場合があります。")
    if provider == "openai":
        openai_key = st.text_input(
            "OPENAI_API_KEY",
            type="password",
            help="OpenAI のAPIキー。環境変数ではなくここに直接入力してもOK"
        )
        openai_base_url = st.text_input(
            "OPENAI_BASE_URL (任意)",
            value="",
            help="互換API/プロキシを使う場合に設定（http/httpsで始まるURL）。未入力なら公式エンドポイント"
        )
    elif provider == "azure":
        azure_key = st.text_input(
            "AZURE_OPENAI_API_KEY",
            type="password",
            help="Azure OpenAI リソースのキー"
        )
        azure_endpoint = st.text_input(
            "AZURE_OPENAI_ENDPOINT",
            value="https://<your-resource>.openai.azure.com/",
            help="Azure OpenAI リソースのエンドポイントURL"
        )
        azure_api_version = st.text_input(
            "AZURE_OPENAI_API_VERSION",
            value="2024-08-01-preview",
            help="利用するAPIバージョン（例: 2024-08-01-preview）"
        )
    else:
        openai_key = ""
        openai_base_url = ""
        azure_key = ""
        azure_endpoint = ""
        azure_api_version = "2024-08-01-preview"

st.subheader("基本情報")
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("プロジェクト名", value="", help="各ドキュメントのタイトルや本文に使用されます")
    sponsor = st.text_input("スポンサー/意思決定者", value="", help="承認・意思決定の責任者（個人名や役職名）")
with col2:
    currency = st.text_input("予算通貨コード", value="JPY", help="ISO通貨コード（例: JPY, USD, EUR）")
    amount = st.number_input("予算額", value=0, min_value=0, step=1000, help="概算でもOK。整数で入力してください")

st.divider()

st.subheader("目的 / スコープ / 制約 / 前提")
st.caption("セルを直接クリックして入力できます。行の追加はテーブル左下の + ボタンから。表示されない場合はページをリロードしてください。")
colA, colB = st.columns(2)
with colA:
    st.caption("目的: プロジェクトで達成したい成果。SMART（具体的・測定可能・達成可能・関連・期限）を意識")
    df_objectives = st.data_editor(
        pd.DataFrame({"objective": [""]}), use_container_width=True, num_rows="dynamic", key="obj", hide_index=True
    )
    st.caption("スコープ（IN）: 対象に含める作業・成果物の例")
    df_scope_in = st.data_editor(
        pd.DataFrame({"in": [""]}), use_container_width=True, num_rows="dynamic", key="sin", hide_index=True
    )
with colB:
    st.caption("スコープ（OUT）: 対象に含めない作業・成果物の例")
    df_scope_out = st.data_editor(
        pd.DataFrame({"out": [""]}), use_container_width=True, num_rows="dynamic", key="sout", hide_index=True
    )
    st.caption("制約: 予算/納期/品質/技術/契約など、満たすべき固定条件")
    df_constraints = st.data_editor(
        pd.DataFrame({"constraint": [""]}), use_container_width=True, num_rows="dynamic", key="cons", hide_index=True
    )

st.caption("前提: 真であると見なす条件（例: 他部署の協力が得られる 等）")
df_assumptions = st.data_editor(
    pd.DataFrame({"assumption": [""]}), use_container_width=True, num_rows="dynamic", key="ass", hide_index=True
)

st.subheader("マイルストーン / ステークホルダー / リスクの種")
colM, colS = st.columns(2)
with colM:
    st.caption("マイルストーン: 重要な到達点。targetは日付や期間（例: 2025-12-31）")
    df_milestones = st.data_editor(
        pd.DataFrame({"name": [""], "target": [""]}), use_container_width=True, num_rows="dynamic", key="ms", hide_index=True
    )
with colS:
    st.caption("ステークホルダー: 利害関係者の名前と関心事（期待/懸念など）")
    df_stakeholders = st.data_editor(
        pd.DataFrame({"name": [""], "interest": [""]}), use_container_width=True, num_rows="dynamic", key="sh", hide_index=True
    )

st.caption("リスクの種: 具体化するとリスクとなり得る事柄（例: 主要メンバーの離任）")
df_risks = st.data_editor(
    pd.DataFrame({"risk": [""]}), use_container_width=True, num_rows="dynamic", key="risk", hide_index=True
)

extended_data: Dict[str, Any] = {}
if level == "extended":
    st.divider()
    st.subheader("会社標準（拡張項目）")
    colE1, colE2 = st.columns(2)
    with colE1:
        project_code = st.text_input("社内プロジェクトコード", value="", help="社内台帳・経理で用いる識別子があれば入力")
        department = st.text_input("主担当部門", value="", help="責任部門・主管部門など")
        st.caption("受入条件: 完了判定に用いる基準（例: 合否条件、テスト合格条件）")
        df_acceptance = st.data_editor(
            pd.DataFrame({"acceptance": [""]}), use_container_width=True, num_rows="dynamic", key="acc", hide_index=True
        )
        st.caption("非機能要件(NFR): 性能/可用性/運用性/セキュリティ/拡張性など")
        df_nfr = st.data_editor(
            pd.DataFrame({"nfr": [""]}), use_container_width=True, num_rows="dynamic", key="nfr", hide_index=True
        )
        st.caption("順守事項: 法令/社内規程/業界標準 等")
        df_compliance = st.data_editor(
            pd.DataFrame({"compliance": [""]}), use_container_width=True, num_rows="dynamic", key="comp", hide_index=True
        )
    with colE2:
        data_classification = st.text_input(
            "データ区分(公開/社外秘/機密)",
            value="",
            help="情報の機密区分や取扱レベル（例: 公開/社外秘/機密）"
        )
        st.caption("コミュニケーション頻度: 定例/週次/日次 などの運用リズム")
        df_cadence = st.data_editor(
            pd.DataFrame({"cadence": [""]}), use_container_width=True, num_rows="dynamic", key="cad", hide_index=True
        )
        st.caption("依存関係: 他案件・他部門・外部要因への依存")
        df_dependencies = st.data_editor(
            pd.DataFrame({"dependency": [""]}), use_container_width=True, num_rows="dynamic", key="dep", hide_index=True
        )
        st.caption("WBS: 成果物（deliverable）と、その配下の作業（work_packages）をカンマ区切りで入力")
        df_wbs = st.data_editor(
            pd.DataFrame({"deliverable": [""], "work_packages(comma)": [""]}),
            use_container_width=True,
            num_rows="dynamic",
            key="wbs",
            hide_index=True,
        )

    ccb = st.text_input("CCB(変更管理委員会)の有無/構成", value="", help="意思決定機関の有無、メンバー、開催頻度など")
    esc = st.text_input("エスカレーション先", value="", help="重大問題発生時の連絡先・指揮系統")

    extended_data = {
        "project_code": project_code,
        "department": department,
        "acceptance_criteria": [x for x in df_acceptance["acceptance"].astype(str).tolist() if x],
        "non_functional_requirements": [x for x in df_nfr["nfr"].astype(str).tolist() if x],
        "compliance_requirements": [x for x in df_compliance["compliance"].astype(str).tolist() if x],
        "data_classification": data_classification,
        "communication_cadence": [x for x in df_cadence["cadence"].astype(str).tolist() if x],
        "dependencies": [x for x in df_dependencies["dependency"].astype(str).tolist() if x],
        "wbs": [
            {
                "deliverable": row.get("deliverable", ""),
                "work_packages": [p.strip() for p in str(row.get("work_packages(comma)", "")).split(",") if p.strip()],
            }
            for _, row in df_wbs.iterrows()
            if any(str(v).strip() for v in row.values)
        ],
        "governance": {"change_control_board": ccb, "escalation_path": esc},
    }

# JSONの組み立て
payload: Dict[str, Any] = {
    "name": name,
    "sponsor": sponsor,
    "objectives": [x for x in df_objectives["objective"].astype(str).tolist() if x],
    "scope": {
        "in": [x for x in df_scope_in["in"].astype(str).tolist() if x],
        "out": [x for x in df_scope_out["out"].astype(str).tolist() if x],
    },
    "constraints": [x for x in df_constraints["constraint"].astype(str).tolist() if x],
    "assumptions": [x for x in df_assumptions["assumption"].astype(str).tolist() if x],
    "milestones": [
        {"name": str(row.get("name", "")), "target": str(row.get("target", ""))}
        for _, row in df_milestones.iterrows()
        if any(str(v).strip() for v in row.values)
    ],
    "budget": {"currency": currency, "amount": int(amount or 0)},
    "stakeholders": [
        {"name": str(row.get("name", "")), "interest": str(row.get("interest", ""))}
        for _, row in df_stakeholders.iterrows()
        if any(str(v).strip() for v in row.values)
    ],
    "risk_seeds": [x for x in df_risks["risk"].astype(str).tolist() if x],
}

if level == "extended":
    payload.update(extended_data)

# 操作ボタン
col_btn1, col_btn2, col_btn3 = st.columns([1,1,1])
with col_btn1:
    if st.button("JSONプレビュー"):
        status_prev = st.empty()
        status_prev.info("作業中...")
        with st.spinner("作業中... しばらくお待ちください"):
            st.code(json.dumps(payload, ensure_ascii=False, indent=2), language="json")
        status_prev.success("プレビューを表示しました")
with col_btn2:
    if st.button("保存"):
        status_save = st.empty()
        status_save.info("作業中...")
        with st.spinner("作業中... 保存しています"):
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            Path(out_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        status_save.success("保存が完了しました")
        st.success(f"保存しました: {out_path}")
with col_btn3:
    st.download_button(
        label="JSONダウンロード",
        file_name=Path(out_path).name,
        mime="application/json",
        data=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
    )

st.divider()

st.subheader("（任意）テキストドキュメントの生成")
col_gen1, col_gen2 = st.columns(2)
with col_gen1:
    doc_type = st.selectbox(
        "doc_type",
        options=[
            "project_charter",
            "scope_statement",
            "wbs_outline",
            "schedule_overview",
            "risk_management_plan",
            "stakeholder_register",
            "communication_plan",
            "quality_management_plan",
            "procurement_plan",
            "change_management_plan",
            "lessons_learned",
        ],
        index=0,
        help="生成するドキュメント種別を選択（例: project_charter=プロジェクト憲章, scope_statement=スコープ記述）"
    )
    out_doc = st.text_input("出力先(txt)", value="output/from_ui.txt", help="生成結果のテキスト保存先パス")
    input_source = st.radio(
        "入力ソース",
        options=["現在の画面の内容", "JSONファイルから"],
        index=0,
        help="画面上の入力内容を使うか、既存のJSONファイルを読み込むかを選択"
    )
    uploaded = None
    if input_source == "JSONファイルから":
        uploaded = st.file_uploader("JSONファイルを選択", type=["json"], help="プロジェクト情報のJSONファイルをアップロード")    
with col_gen2:
    language_sel = st.selectbox("言語", options=["ja", "en"], index=0, help="生成するドキュメントの言語")
    note = st.text_input("追加指示(任意)", value="", help="生成時に追加したい指示（口調、章立て、想定読者など）")

if st.button("ドキュメント生成"):
    # 入力ソース切替
    ctx = payload
    if input_source == "JSONファイルから" and uploaded is not None:
        try:
            ctx = json.loads(uploaded.getvalue().decode("utf-8"))
        except Exception as e:
            st.error(f"JSONの読み込みに失敗しました: {e}")
            st.stop()

    # プロバイダ設定を反映
    settings = None
    if provider == "stub":
        settings = AppSettings(model=model, temperature=temperature, max_tokens=int(max_tokens), use_stub=True)
    elif provider == "openai":
        if not openai_key:
            st.error("OPENAI_API_KEY を入力してください。")
            st.stop()
        settings = AppSettings(
            model=model,
            temperature=temperature,
            max_tokens=int(max_tokens),
            use_stub=False,
            use_responses_api=prefer_responses_api,
            fallback_to_stub_on_empty=fallback_stub,
            openai_api_key=openai_key,
            openai_base_url=openai_base_url or None,
        )
    elif provider == "azure":
        if not azure_key or not azure_endpoint:
            st.error("AZURE_OPENAI_API_KEY と AZURE_OPENAI_ENDPOINT を入力してください。")
            st.stop()
        settings = AppSettings(
            model=model,
            temperature=temperature,
            max_tokens=int(max_tokens),
            use_stub=False,
            use_responses_api=prefer_responses_api,
            fallback_to_stub_on_empty=fallback_stub,
            azure_openai_api_key=azure_key,
            azure_openai_endpoint=azure_endpoint,
            azure_openai_api_version=azure_api_version,
        )
    else:
        # stub の場合もフラグを反映（将来の拡張に備えて）
        settings = AppSettings(
            model=model,
            temperature=temperature,
            max_tokens=int(max_tokens),
            use_stub=True,
            use_responses_api=prefer_responses_api,
            fallback_to_stub_on_empty=fallback_stub,
        )

    try:
        Path(Path(out_doc).parent).mkdir(parents=True, exist_ok=True)
        status_placeholder = st.empty()
        status_placeholder.info("作成中...")
        progress_bar = st.progress(0)
        elapsed_placeholder = st.empty()

        def _run_generation():
            return generate_text_document(
                doc_type=doc_type,
                project_context=ctx,
                out_path=out_doc,
                language=language_sel,
                extra_instructions=note,
                settings=settings,
            )

        start_time = time.time()
        percent = 0
        with ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(_run_generation)
            # 疑似的な進行度アニメーション＋経過時間表示
            while not future.done():
                elapsed = time.time() - start_time
                percent = (percent + 3) % 100
                progress_bar.progress(percent)
                elapsed_placeholder.write(f"経過時間: {elapsed:.1f} 秒")
                time.sleep(0.1)
            # 完了処理
            path = future.result()
        progress_bar.progress(100)
        total_elapsed = time.time() - start_time
        status_placeholder.success(f"作成が完了しました（経過 {total_elapsed:.1f} 秒）")
        st.success(f"生成しました: {path}")
        # 生成したテキストの内容をプレビュー表示
        try:
            content = Path(path).read_text(encoding="utf-8")
        except Exception as e:
            st.warning(f"ファイル読み込みに失敗しました: {e}")
        else:
            st.subheader("生成結果プレビュー")
            st.code(content, language="markdown")
    except Exception as e:
        try:
            status_placeholder.error("生成に失敗しました")
        except Exception:
            pass
        st.error(f"生成に失敗しました: {e}")
        # よくある対処のヒントとワンクリック操作
        with st.expander("トラブルシューティングのヒント"):
            st.markdown("- OpenAI を利用中で空出力のエラーの場合は『Responses API を優先』に切り替えて再実行をお試しください。")
            st.markdown("- 空でも処理を継続したい場合は『空出力時にスタブへフォールバック』を有効にしてください。")
            st.markdown("- OPENAI_BASE_URL を設定している場合は https:// で始まる正しいURLかご確認ください（未入力なら公式)。")
        # 自動リトライ（OpenAI×Responses 優先で未実施だった場合のみ）
        try_responses_retry = (provider == "openai") and (not prefer_responses_api)
        if try_responses_retry:
            st.info("Responses API を優先して自動リトライします…")
            try:
                settings_retry = AppSettings(
                    model=model,
                    temperature=temperature,
                    max_tokens=int(max_tokens),
                    use_stub=False,
                    use_responses_api=True,
                    fallback_to_stub_on_empty=fallback_stub,
                    openai_api_key=openai_key,
                    openai_base_url=openai_base_url or None,
                )
                start_time2 = time.time()
                with st.spinner("Responses APIで再試行中..."):
                    path2 = generate_text_document(
                        doc_type=doc_type,
                        project_context=ctx,
                        out_path=out_doc,
                        language=language_sel,
                        extra_instructions=note,
                        settings=settings_retry,
                    )
                total_elapsed2 = time.time() - start_time2
                st.success(f"Responses APIで生成に成功しました（{total_elapsed2:.1f} 秒）: {path2}")
                try:
                    content2 = Path(path2).read_text(encoding="utf-8")
                except Exception as e2:
                    st.warning(f"ファイル読み込みに失敗しました: {e2}")
                else:
                    st.subheader("生成結果プレビュー（リトライ）")
                    st.code(content2, language="markdown")
            except Exception as re:
                st.error(f"Responses APIでのリトライも失敗しました: {re}")
