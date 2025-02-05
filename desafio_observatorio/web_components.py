""" Módulo de componentes web dash """
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.express as px
import pandas as pd

import data_processing
from helpers import (
    VIA,
    MONTHS,
    INDICATOR_OPTIONS,
    OPERATION_OPTIONS,
)

years_options = data_processing.api_get_years_listing()
operation_options = list(OPERATION_OPTIONS.keys())
# também é usado como lista de opções para o dropdown
product_options = data_processing.api_get_ncm_code_listing()
# Preparando os dados da tabela
total_by_state = data_processing.api_get_state_contribution()

# instanciando um app Dash
external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# Algumas configurações do app
app.title = "Dados Comércio Exterior"
pd.options.plotting.backend = "plotly"



app.layout = html.Div(
    [
        #título
        html.H1(
            children='Dashboard Comércio Exterior',
            style={'textAlign': 'center','color':'rgb(23,61,116)'},
        ),

        html.Div([
                html.Img(
                    src=app.get_asset_url('logo.png'),
                    #style={
                      #  'height': '50%',
                     #   'width': '50%'
                    #}
                    )
        ], style={'textAlign': 'center'}),

        #texto filtros
        html.Div(
            children='Filtros para a visualização',
            style={'textAlign': 'center','font-weight': 'bold','font-size': '14px'},
        ),        


        # filtros do gráfico principal
        html.Div(
            [
                # Escolha da movimentação
                dcc.Dropdown(
                    id="operation-options-dropdown",
                    options=[
                        {"label": i, "value": i} for i in operation_options
                    ],
                    value=operation_options[0],
                ),
                # Escolha da UF
                dcc.Dropdown(
                    id="product-options-dropdown",
                    options=[{"label": i, "value": i} for i in product_options],
                    value=product_options[0],
                ),
                # escolha do indicador
                dcc.Dropdown(
                    id="indicator-options-dropdown",
                    options=[{"label": i, "value": i} for i in INDICATOR_OPTIONS],
                    value=INDICATOR_OPTIONS[0],
                ),
                # Slider de seleção do ano
                dcc.Slider(
                    id="year-slider-input",
                    min=min(years_options),
                    max=max(years_options),
                    value=max(years_options),
                    marks={str(year): str(year) for year in years_options},
                    step=None,
                ),
                
            ],
            style={'width': '49%','margin':'auto'},
        ),
        # Visualização principal
        html.Div(
            [dcc.Graph(id="main-scatter-plot")],
            style={},
        ),
        # Gráfico de pizza com a utilização percentual da via
        html.Div(
            [dcc.Graph(id="via-pie-plot")],
            style={},
        ),
        # Tabela com a contribuição percentual dos estados
        html.Div(
            dash_table.DataTable(
                id="percentual-contribution-table",
                columns=[{"name": i, "id": i} for i in total_by_state.columns],
                data=total_by_state.to_dict("records"),
                #setando os valores das colunas     
                style_cell_conditional=[
                    {
                        'if': {'column_id': c},
                        'width': '8%'}
                        for c in ['SG_UF','VL_KG_CONTRIB_%']
                    
                    ],
                # visualização sem o grid
                style_as_list_view=True,
                #header preto
                style_header={'backgroundColor': 'rgb(30, 30, 30)','color': 'white'},
                fill_width=False,     
                
            ),
            #estilos da div da tabela
            style={'margin-left': '50px','margin-right':'50px'}
        )

    ]
)


################################### CALLBACKS ###################################


@app.callback(
    dash.dependencies.Output("main-scatter-plot", "figure"),
    [
        dash.dependencies.Input("operation-options-dropdown", "value"),
        dash.dependencies.Input("indicator-options-dropdown", "value"),
        dash.dependencies.Input("product-options-dropdown", "value"),
        dash.dependencies.Input("year-slider-input", "value"),
    ],
)
def update_main_plot(
    operation: str,
    indicator: str,
    product_value: str,
    year_value: int,
):
    """Atualiza o gráfico principal

    Argumentos:
        operation (str):  [Movimentação selecionada (importação ou exportação)]
        indicator (str):  [Métrica selecionada (valor, valor por peso, etc)]
        product_value (str):   [Categoria de produto selecionado]
        year_value (int): [Ano selecionado]
    """

    response: dict = data_processing.api_get_operation_statistics(
        year_value, OPERATION_OPTIONS[operation], product_value
    )

    df = pd.DataFrame.from_dict(response)

    fig = df.plot(
        kind="bar",
        y=indicator,
    )

    # Configurações dos axes
    # https://plotly.com/python/axes/#set-axis-title-text-with-plotly-express

    # Como formatar os ticks
    # https://plotly.com/python/tick-formatting/

    fig.update_layout(
        xaxis=dict(tickmode="array", tickvals=list(range(13)), ticktext=MONTHS)
    )

    return fig


@app.callback(
    dash.dependencies.Output("via-pie-plot", "figure"),
    [
        dash.dependencies.Input("operation-options-dropdown", "value"),
        dash.dependencies.Input("product-options-dropdown", "value"),
        dash.dependencies.Input("year-slider-input", "value"),
    ],
)
def update_via_pie_plot(
    operation: str,
    product_value: str,
    year_value: int,
):
    """Atualiza o gráfico de pizza
    com a utilização percentual da via.

    Argumentos:
        operation (str):  [Movimentação selecionada (importação ou exportação)]
        indicator (str):  [Métrica selecionada (valor, valor por peso, etc)]
        uf_value (str):   [Estado selecionada]
        year_value (int): [Ano selecionado]
    """

    title = "Utilização percentual da via"

    # condições de filtro são o ano e o tipo de movimeentação
    response: dict = data_processing.api_get_via_statistics_statistics(
        year_value, OPERATION_OPTIONS[operation], product_value
    )
    df = pd.DataFrame.from_dict(response)

    # Personalizações do pie chart
    # https://plotly.com/python/pie-charts/
    fig = px.pie(df, values="as_percentage", names="code", title=title)

    return fig