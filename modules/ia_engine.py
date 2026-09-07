import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.inspection import permutation_importance
import shap
from config.i18n import t
from config.settings import RANDOM_STATE, TEST_SIZE

def cargar_archivo():
    archivo = st.file_uploader(t("subir_archivo", st.session_state.idioma),
                              type=["csv", "geojson", "parquet"])
    if archivo:
        if archivo.name.endswith(".csv"):
            return pd.read_csv(archivo)
        elif archivo.name.endswith(".parquet"):
            return pd.read_parquet(archivo)
        elif archivo.name.endswith(".geojson"):
            import geopandas as gpd
            return gpd.read_file(archivo)
    return None

def analisis_exploratorio(df):
    st.subheader("📊 " + t("eda_titulo", st.session_state.idioma))
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**{t('filas', st.session_state.idioma)}:** {df.shape[0]}")
        st.write(f"**{t('columnas', st.session_state.idioma)}:** {df.shape[1]}")
        st.dataframe(df.describe(), use_container_width=True)
    with col2:
        st.write("**Tipos de datos:**")
        st.dataframe(pd.DataFrame(df.dtypes, columns=["Tipo"]), use_container_width=True)

    # Matriz de correlación
    numericas = df.select_dtypes(include=[np.number]).columns
    if len(numericas) >= 3:
        st.subheader(t("correlaciones", st.session_state.idioma))
        corr = df[numericas].corr()
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(corr, cmap="RdBu_r", vmin=-1, vmax=1, annot=True, fmt=".2f", ax=ax)
        st.pyplot(fig)
        st.info(t("interpretacion_corr", st.session_state.idioma))

    return numericas

def entrenar_y_evaluar(X, y, espacial=False):
    modelos = {
        "Random Forest": RandomForestRegressor(random_state=RANDOM_STATE),
        "XGBoost": XGBRegressor(random_state=RANDOM_STATE, objective="reg:squarederror")
    }
    resultados = {}
    mejor_nombre, mejor_r2 = None, -np.inf

    for nombre, modelo in modelos.items():
        if espacial:
            st.info(f"✅ {t('validacion_espacial', st.session_state.idioma)}")
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, shuffle=False)
        else:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE)

        # Ajuste de hiperparámetros
        if nombre == "Random Forest":
            params = {"n_estimators": [100, 200], "max_depth": [8, 12, None]}
        else:
            params = {"n_estimators": [100, 200], "max_depth": [4, 8], "learning_rate": [0.05, 0.1]}

        busqueda = GridSearchCV(modelo, params, cv=5, scoring="r2", n_jobs=-1)
        busqueda.fit(X_train, y_train)
        y_pred = busqueda.predict(X_test)

        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)

        resultados[nombre] = {
            "mejor_modelo": busqueda.best_estimator_,
            "mejores_parametros": busqueda.best_params_,
            "R²": round(r2, 4),
            "RMSE": round(rmse, 4),
            "MAE": round(mae, 4),
            "y_test": y_test, "y_pred": y_pred, "X_test": X_test
        }

        if r2 > mejor_r2:
            mejor_r2 = r2
            mejor_nombre = nombre

    return resultados, mejor_nombre

def calcular_explicabilidad(modelo, X, nombres_caracteristicas):
    st.subheader("🔍 " + t("explicabilidad", st.session_state.idioma))

    # Importancia por permutación
    imp = permutation_importance(modelo, X, n_repeats=10, random_state=RANDOM_STATE)
    df_imp = pd.DataFrame({"Característica": nombres_caracteristicas,
                            "Importancia": imp.importances_mean}).sort_values("Importancia", ascending=False)
    st.dataframe(df_imp, use_container_width=True)

    # Valores SHAP
    try:
        explainer = shap.Explainer(modelo.predict, X[:100])
        shap_values = explainer(X[:100])
        st.subheader("Valores SHAP")
        fig, ax = plt.subplots(figsize=(8, 4))
        shap.plots.beeswarm(shap_values, show=False)
        st.pyplot(fig)
        st.info(t("shap_interpretacion", st.session_state.idioma))
    except Exception as e:
        st.warning(f"SHAP: {e}")

def interfaz_motor_ia():
    st.header("🤖 " + t("motor_ia_titulo", st.session_state.idioma))
    df = cargar_archivo()
    if df is None:
        st.info(t("cargar_datos_ia", st.session_state.idioma))
        return

    numericas = analisis_exploratorio(df)
    if len(numericas) < 2:
        st.warning(t("no_datos_numericos", st.session_state.idioma))
        return

    st.subheader(t("config_modelado", st.session_state.idioma))
    objetivo = st.selectbox(t("variable_objetivo", st.session_state.idioma), numericas)
    caracteristicas = st.multiselect(t("caracteristicas", st.session_state.idioma),
                                     [c for c in numericas if c != objetivo],
                                     default=[c for c in numericas if c != objetivo][:4])
    validacion_espacial = st.checkbox(t("usar_validacion_espacial", st.session_state.idioma))

    if st.button("🚀 " + t("entrenar", st.session_state.idioma), type="primary"):
        X = df[caracteristicas].dropna()
        y = df.loc[X.index, objetivo]

        resultados, mejor_nombre = entrenar_y_evaluar(X, y, espacial=validacion_espacial)

        st.subheader("📈 " + t("resultados_modelos", st.session_state.idioma))
        resumen = pd.DataFrame({k: {"R²": v["R²"], "RMSE": v["RMSE"], "MAE": v["MAE"]}
                                for k, v in resultados.items()}).T
        st.dataframe(resumen.style.highlight_max(subset=["R²"]).highlight_min(subset=["RMSE","MAE"]),
                     use_container_width=True)

        st.success(f"🏆 {t('mejor_modelo', st.session_state.idioma)}: **{mejor_nombre}**")
        mejor = resultados[mejor_nombre]
        st.write(f"**{t('parametros', st.session_state.idioma)}:**", mejor["mejores_parametros"])

        # Gráfico Predicción vs Real
        fig, ax = plt.subplots()
        ax.scatter(mejor["y_test"], mejor["y_pred"], alpha=0.6)
        minv, maxv = mejor["y_test"].min(), mejor["y_test"].max()
        ax.plot([minv, maxv], [minv, maxv], "r--", label="Línea ideal")
        ax.set_xlabel(t("valor_real", st.session_state.idioma))
        ax.set_ylabel(t("valor_predicho", st.session_state.idioma))
        ax.legend()
        st.pyplot(fig)

        calcular_explicabilidad(mejor["mejor_modelo"], mejor["X_test"], caracteristicas)
