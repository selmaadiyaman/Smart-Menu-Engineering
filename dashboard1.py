# -----------------------------
# Gerekli kütüphaneler
# -----------------------------
import pyodbc
import pandas as pd
from dash import Dash, html, dcc, dash_table
from dash.dependencies import Input, Output
import plotly.express as px

# -----------------------------
# MSSQL’den veri çekme ve Menü Analizi
# -----------------------------
def get_menu_data():
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=.\\SQLEXPRESS;"
        "DATABASE=SmartMenuDB;"
        "Trusted_Connection=yes;"
    )
    conn = pyodbc.connect(conn_str)
    query_sales = """
    SELECT s.SaleDate, m.ItemName, s.Quantity, m.Price, m.Cost
    FROM Sales s
    JOIN MenuItem m ON s.ItemID = m.ItemID
    """
    df = pd.read_sql(query_sales, conn)
    conn.close()

    # Hesaplamalar
    df['ContributionMargin'] = df['Price'] - df['Cost']
    total_sales = df.groupby('ItemName')['Quantity'].sum().reset_index()
    total_sales.rename(columns={'Quantity': 'TotalQuantity'}, inplace=True)
    total_sales['Popularity'] = total_sales['TotalQuantity'] / total_sales['TotalQuantity'].sum()
    avg_cm = df.groupby('ItemName')['ContributionMargin'].mean().reset_index()
    avg_cm.rename(columns={'ContributionMargin': 'AvgCM'}, inplace=True)
    menu_analysis = total_sales.merge(avg_cm, on='ItemName')

    # Sınıflandırma
    cm_median = menu_analysis['AvgCM'].median()
    pop_median = menu_analysis['Popularity'].median()

    def classify(row):
        if row['Popularity'] >= pop_median and row['AvgCM'] >= cm_median:
            return 'Star'
        elif row['Popularity'] >= pop_median and row['AvgCM'] < cm_median:
            return 'Plowhorse'
        elif row['Popularity'] < pop_median and row['AvgCM'] >= cm_median:
            return 'Puzzle'
        else:
            return 'Dog'

    menu_analysis['Category'] = menu_analysis.apply(classify, axis=1)

    return menu_analysis  # <-- BURAYI EKLEDİK


# DataFrame
df = get_menu_data()

# -----------------------------
# Dash Uygulaması
# -----------------------------
app = Dash(__name__)

# Başlangıç scatterplot
def create_figure(dataframe):
    fig = px.scatter(
        dataframe,
        x='Popularity',
        y='AvgCM',
        color='Category',
        text='ItemName',
        color_discrete_map={'Star': 'green', 'Plowhorse': 'blue', 'Puzzle': 'orange', 'Dog': 'red'},
        labels={'Popularity': 'Popülerlik (%)', 'AvgCM': 'Ortalama Katkı Payı (TL)'},
        title='Menu Engineering Matrix'
    )
    fig.update_traces(textposition='top center',
                      marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey')))
    return fig

# Layout
app.layout = html.Div([
    html.H1("Menu Engineering Dashboard", style={'textAlign': 'center'}),

    html.Div([
        html.Label("Kategori Filtre:"),
        dcc.Dropdown(
            id='category-dropdown',
            options=[{'label': c, 'value': c} for c in ['All', 'Star', 'Plowhorse', 'Puzzle', 'Dog']],
            value='All'
        )
    ], style={'width': '25%', 'margin': '20px'}),

    dcc.Graph(id='matrix-graph', figure=create_figure(df)),

    html.H2("Ürün Tablosu"),
    dash_table.DataTable(
        id='menu-table',
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        style_cell={'textAlign': 'center'},
        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
        page_size=20
    )
])

# Callback: Filtreleme
@app.callback(
    Output('matrix-graph', 'figure'),
    Output('menu-table', 'data'),
    Input('category-dropdown', 'value')
)
def update_dashboard(selected_category):
    filtered_df = df.copy()
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['Category'] == selected_category]

    fig = create_figure(filtered_df)
    table_data = filtered_df.to_dict('records')
    return fig, table_data

# -----------------------------
# Uygulama çalıştır
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)
