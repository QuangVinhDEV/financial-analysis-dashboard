from flask import Flask, render_template, request
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import plotly

app = Flask(__name__)

# Đọc dữ liệu từ Google Drive
file_id = "1c86oGKKV36PtGLGQNiHA0NfPakuHz8to"
data_path = f"https://drive.google.com/uc?id={file_id}"
df = pd.read_csv(data_path)
df["Order Date"] = pd.to_datetime(df["Order Date"])

@app.route('/', methods=["GET", "POST"])
def index():
    filtered_df = df.copy()
    theme = request.form.get("theme", 'light')
    years = sorted([int(y) for y in filtered_df['Order Date'].dt.year.unique()])

    style_date = 'All'
    time_value = 'All'
    region = 'All'
    status = 'All'
    # --- Nếu có POST (filter) ---
    if request.method == "POST":

        style_date = request.form.get("style_date")
        time_value = request.form.get("time_value")
        region = request.form.get("region")
        status = request.form.get("status")

        # Lọc theo vùng
        if region and region != "All":
            filtered_df = filtered_df[filtered_df["Region"] == region]

        # Lọc theo trạng thái đơn hàng (ví dụ "Sales Channel")
        if status and status != "All":
            filtered_df = filtered_df[filtered_df["Sales Channel"] == status]


        # Filter time
        if style_date =="Year" and time_value != "ALL":
            filtered_df = filtered_df[df['Order Date'].dt.year == int(time_value)]
        if style_date == "Month" and time_value != 'All':
            filtered_df = filtered_df[df["Order Date"].dt.month == int(time_value)]
        if style_date == "Quarter" and time_value != "All":
            qmap = {
                "Q1": [1,2,3],
                "Q2": [4,5,6],
                "Q3": [7,8,9],
                "Q4": [10,11,12],
            }
            filtered_df = filtered_df[df["Order Date"].dt.month.isin(qmap[time_value])]
    style_date = request.form.get("style_date")
    # --- Chart 1: Revenue by month, quarter, year ---
    df_month = (
        filtered_df.groupby(filtered_df["Order Date"].dt.to_period("M"))["Total Revenue"]
        .sum()
        .reset_index()
    )
    df_month["Order Date"] = df_month["Order Date"].astype(str)
    fig1 = px.bar(df_month, x="Order Date", y="Total Revenue",
                  title=f"Revenue By {style_date}", color_discrete_sequence=["#3b82f6"])
    fig1.update_layout(    template="plotly_dark" if theme == "dark" else "plotly_white",
    paper_bgcolor="black" if theme == "dark" else "white",
    plot_bgcolor="black" if theme == "dark" else "white", hovermode="x unified")

    # --- Chart 2: Revenue by region ---
    df_region = filtered_df.groupby("Region")["Total Revenue"].sum().reset_index()
    fig2 = px.pie(df_region, values="Total Revenue", names="Region",
                  title="Revenue By Region",
                  color_discrete_sequence=px.colors.qualitative.Pastel)
    fig2.update_layout(template="plotly_dark" if theme == "dark" else "plotly_white",
    paper_bgcolor="black" if theme == "dark" else "white",
    plot_bgcolor="black" if theme == "dark" else "white")
    
    # --- Chart 3: Revenue Trend
    df_revenue_trend = filtered_df.groupby(filtered_df["Order Date"].dt.to_period("M"))["Total Revenue"].sum().reset_index()
    df_revenue_trend["Order Date"] = df_revenue_trend["Order Date"].astype(str)
    fig3 = px.line(df_revenue_trend,x="Order Date", y='Total Revenue', labels=df_revenue_trend["Total Revenue"], title=f"Revenue Trend by {style_date}")
    fig3.update_layout(template="plotly_dark" if theme == "dark" else "plotly_white",
    paper_bgcolor="black" if theme == "dark" else "white",
    plot_bgcolor="black" if theme == "dark" else "white")

    # --- Chart 4: Heatmap Score
    df_heat_map = filtered_df.groupby(filtered_df["Country"])["Total Revenue"].sum().reset_index()
    fig4 = px.choropleth(df_heat_map,locations="Country", locationmode="country names", color="Total Revenue", color_continuous_scale='Viridis', title="HeatMap: Country")
    fig4.update_layout(template="plotly_dark" if theme == "dark" else "plotly_white",
    paper_bgcolor="black" if theme == "dark" else "white",
    plot_bgcolor="black" if theme == "dark" else "white")

    # --- Chart 5: 
    df_sales_channel = filtered_df.groupby(filtered_df["Sales Channel"])["Total Revenue"].sum().reset_index()
    fig5 = px.bar(df_sales_channel, x="Sales Channel", y="Total Revenue", title="Revenue By Channel", color_discrete_sequence=["#3b82f6"])
    fig5.update_layout(       template="plotly_dark" if theme == "dark" else "plotly_white",
        paper_bgcolor="black" if theme == "dark" else "white",
        plot_bgcolor="black" if theme == "dark" else "white", hovermode="x unified")

    total_revenue = round(filtered_df["Total Revenue"].sum(), 2)
    total_profit = round(filtered_df["Total Profit"].sum(), 2)
    total_cost = round(filtered_df["Total Cost"].sum(), 2)

    cogs_rate = round(-1 * (total_cost / total_revenue) * 100, 2)
    profit_rate = round(100 + cogs_rate, 2)

    avg_unit_price = round(filtered_df["Unit Price"].mean(), 2)

    formatted_total_revenue = f"{total_revenue:,.2f}"
    formatted_total_profit = f"{total_profit:,.2f}"
    formatted_total_cost = f"{total_cost:,.2f}"
    formatted_avg_unit_price = f"{avg_unit_price:,.2f}"
    formatted_cogs_rate = f"{cogs_rate:,.2f}%"
    formatted_profit_rate = f"{profit_rate:,.2f}%"

    

    graphJSON4= json.dumps(fig4, cls=plotly.utils.PlotlyJSONEncoder)
    # --- HTML Chart ---
    chart1_html = fig1.to_html(full_html=False)
    chart2_html = fig2.to_html(full_html=False)
    chart3_html = fig3.to_html(full_html=False)
    chart5_html = fig5.to_html(full_html=False)

    # Danh sách filter cho select box
    regions = ["All"] + sorted(df["Region"].unique().tolist())
    statuses = ["All"] + sorted(df["Sales Channel"].unique().tolist())
    years = sorted([int(y) for y in df["Order Date"].dt.year.unique()])

    current_time = datetime.now().strftime("%H:%M:%S %d/%m/%y")

    return render_template("index.html",
                           years=years,
                           chart1=chart1_html,
                           chart2=chart2_html,
                           chart3=chart3_html,
                           chart5=chart5_html,
                           graphJSON4=graphJSON4,
                           regions=regions,
                           statuses=statuses,
                           selected_style=style_date,
                           selected_time=time_value,
                           selected_region=region,
                           selected_status=status,
                           current_time=current_time,
                            total_revenue=formatted_total_revenue,
                            total_profit=formatted_total_profit,
                            total_cost=formatted_total_cost,
                            avg_unit_price=formatted_avg_unit_price,
                            cogs_rate=formatted_cogs_rate,
                            profit_rate=formatted_profit_rate,
                           theme=theme)

@app.route("/export")
def export():
    filter_df = get_current_filtered_data()
    csv = filtered_df.to_csv(index=False)
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=sales_export.csv"}
    )
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
