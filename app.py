import faicons as fa
import pandas as pd
import plotly.express as px
import numpy as np
import io
from shared import app_dir, lgbtq, cv_resourceType, cv_producer, cv_themes, cv_subject, cv_country, cv_region, cv_adminLevel, cv_unitAnalysis,cv_longitudinal, cv_language, cv_restrictions, pub_min, pub_max

from shinywidgets import output_widget, render_plotly
from shiny import App, reactive, render, ui
import shinyswatch


ICONS = {
    "table":fa.icon_svg("table-list"),
    "calculator": fa.icon_svg("calculator"),
    "clock": fa.icon_svg("clock")
}

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.include_css("www/style.css"),
        
        ui.input_selectize(
            "select_themes",
            "Select theme",
            cv_themes,
            multiple=False,
            selected="All"
        ),
        ui.input_selectize(
            "select_region",
            "Select region(s)",
            cv_region,
            multiple=True,
            selected="All"
        ),
        ui.input_slider(
            "select_pub_year", 
            "Publication year(s)", 
            min=pub_min, 
            max=pub_max,
            value=[pub_min,pub_max],
            sep = None,
            ),        

        ui.input_selectize(
            "select_lang",
            "Select language(s)",
            cv_language,
            multiple=True,
            selected="All"
        ),
        ui.input_text("free_text", "Search for text", "Enter text..."),   
        ui.input_selectize(
            "select_retype",
            "Select a Resource Type",
            cv_resourceType,
            selected="All"
        ),
        bg="#f8f8f8"),  
    ui.navset_pill(  
        ui.nav_panel("Overview", 
                     ui.layout_column_wrap(
                         ui.value_box("Number of resources",ui.output_text("selected_entries")),
                         
                    fill=False,),
                    ui.layout_column_wrap(
                        ui.card("Top resource types in selection",ui.output_data_frame("top_resourcetypes")),
                        ui.card("Top regions in selection", output_widget("regions_pie")), 

                    fill=False),
                     ),
        ui.nav_panel("Explore resources", 
                     ui.layout_columns(
                         ui.card(
                             
                              ui.card_header("Resources overview"),
                              ui.div(
                                  ui.download_button("download_filtered", label="Download filtered data as .csv", class_="btn-primary"),
                                  ui.input_action_button("grid_details","Show details for selected row")),
                              
                              ui.output_data_frame("grid_table"),                              
                          ),
                                             
                    ),
                    
                    ),
        ui.nav_panel("About this page", "Panel C content"),
        id="tab"
    ),
    theme=shinyswatch.theme.lux,
    window_title="Representation in data",
    title=ui.tags.div(ui.tags.p(ui.tags.img(src="logo.png", height="30px"), "   IASSIST Representation in Data Dashboard")),
    )

def server(input, output, session):
    @reactive.calc
    def filtered_data():
        # filter for the ResourceType
        if input.select_retype() == "All":
            filt_resourcetype = (lgbtq["ResourceType"]!= "All") | (lgbtq["ResourceType"].isnull())
        else:
            filt_resourcetype = (lgbtq["ResourceType"].notnull()) & (lgbtq["ResourceType"].str.contains(input.select_retype()))
        
        # filter for PubYear
        filt_pubyear = (lgbtq["PubDate"].isnull()) | (lgbtq["PubDate"].between(input.select_pub_year()[0],input.select_pub_year()[1]))

        # filter for Theme
        if input.select_themes() == "All":
            filt_themes = (lgbtq["Themes"] != "All") | (lgbtq["Themes"].isnull())
        else:
            filt_themes = (lgbtq["Themes"].notnull()) & (lgbtq["Themes"].str.contains(input.select_themes()))

        # filter for language
        if ''.join(input.select_lang()) == "All":
            filt_lang = (lgbtq["Language"] != "All") | (lgbtq["Language"].isnull())
        else:
            filt_lang = (lgbtq["Language"].notnull()) & (lgbtq["Language"].isin(list(input.lang())))
        
        # filter for Region
        if ''.join(input.select_region()) == "All":
            filt_region = (lgbtq["GeographicRegion"] != "All") | (lgbtq["GeographicRegion"].isnull())
        else:
            filt_region = (lgbtq["GeographicRegion"].notnull()) & (lgbtq["GeographicRegion"].isin(list(input.select_region())))
        # free text input
        if input.free_text() == "Enter text...":
            filt_free = (lgbtq["GeographicRegion"] !="All") | (lgbtq["GeographicRegion"].isnull())
        else:
            filt_free = (lgbtq.apply(lambda row: row.astype(str).str.contains(input.free_text()).any(), axis=1))

        return lgbtq.loc[filt_resourcetype & filt_themes & filt_region & filt_free & filt_lang & filt_pubyear]
    
    @render.text
    def selected_entries():
        return filtered_data().shape[0]
    
    @render.data_frame
    def top_resourcetypes():
        top_restypes = pd.DataFrame(filtered_data()["ResourceType"].value_counts().head(10))
        top_restypes.reset_index(drop=False, inplace=True)
        top_restypes.rename(columns={"ResourceType":"Resource Type"}, inplace=True)
        return render.DataGrid(top_restypes) 
    
    @render.data_frame
    def top_regions(): # not used
        top_regs = pd.DataFrame(filtered_data()["GeographicRegion"].value_counts().head(10))
        top_regs.reset_index(drop=False, inplace=True)
        top_regs.rename(columns={"GeographicRegion":"Region"}, inplace=True)
        return render.DataGrid(top_regs)
    
    @render_plotly
    def regions_pie():
        top_regs = pd.DataFrame(filtered_data()["GeographicRegion"].value_counts().head(10))
        top_regs.reset_index(drop=False, inplace=True)
        top_regs.rename(columns={"GeographicRegion":"Region"}, inplace=True)
        regs_fig = px.pie(top_regs, values='count', names='Region')
        return regs_fig

# create the spreadsheet for "Explore resources" tab
    @render.data_frame 
    def grid_table():
        cols = ['ID','Title', 'ResourceType', 'PubDate',
       'GeographicRegion','Language', 'Themes',
       'Subjects']
        
        return render.DataGrid(filtered_data()[cols], 
                                selection_mode="row", 
                                filters=True)
    
# details on the selected resource
    @render.text
    def grid_detail_description():
        selected = grid_table.data_view(selected=True)["ID"]-1
        description = lgbtq.loc[selected,"Description"].sum()
        return description
    
    @render.ui
    def grid_detail_url():
        selected = grid_table.data_view(selected=True)["ID"]-1
        url = lgbtq.loc[selected,"URL"].sum()
        return ui.a(f"{url}",href=f"{url}", target="_blank")
    
    @render.ui
    def grid_detail_dates():
        selected = grid_table.data_view(selected=True)["ID"]-1
        start = lgbtq.loc[selected,"CollectDateStart"].astype(int).sum()
        end = lgbtq.loc[selected,"CollectDateEnd"].astype(int).sum()
        span = lgbtq.loc[selected,"TimeSpan"].sum()
        longitudinal = lgbtq.loc[selected,"Longitudinal"].sum()
        return ui.div(ui.p(f"Longitudinal? {longitudinal}"),ui.p(f"Data collection: {str(start)} - {str(end)}"), ui.p(f"Temporal coverage: {span}"))

    @render.ui
    def grid_detail_geoadmin():
        selected = grid_table.data_view(selected=True)["ID"]-1
        country = lgbtq.loc[selected,"Country"].sum()
        region = lgbtq.loc[selected,"GeographicRegion"].sum()
        admin = lgbtq.loc[selected,"AdminLevel"].sum()
        return ui.div(ui.p(f"Country: {country}"), ui.p(f"Geographic region: {region}"), ui.p(f"Administrative level: {admin}"))

    @render.ui
    def grid_detail_method():
        selected = grid_table.data_view(selected=True)["ID"]-1
        method = lgbtq.loc[selected,"DataMethodType"].sum()
        unit = lgbtq.loc[selected,"UnitAnalysis"].sum()
        return ui.div(ui.p(f"Methods: {method}"),ui.p(f"Unit of analysis: {unit}"))
    
    @render.ui
    def grid_detail_themes():
        selected = grid_table.data_view(selected=True)["ID"]-1
        themes = lgbtq.loc[selected,"Themes"].sum()
        subjects = lgbtq.loc[selected,"Subjects"].sum()
        return ui.div(ui.p(f"Themes: {themes}"),ui.p(f"Subjects: {subjects}"))

    @render.ui
    def grid_detail_further():
        selected = grid_table.data_view(selected=True)["ID"]-1
        producer = lgbtq.loc[selected,"Producer"].sum()
        distributor = lgbtq.loc[selected,"Distributor"].sum()
        restrictions = lgbtq.loc[selected,"Restrictions"].sum()
        notes = lgbtq.loc[selected,"Notes"].sum()
        return ui.div(ui.p(f"Producer: {producer}"),ui.p(f"Distributor: {distributor}"),ui.p(f"Restrictions? {restrictions}"),ui.p(f"Note: {notes}"))

        



# details popup
    @reactive.effect
    @reactive.event(input.grid_details)
    def _():
        m = ui.modal(
            ui.accordion(
                ui.accordion_panel("URL",ui.output_ui("grid_detail_url")),
                ui.accordion_panel("Description",ui.output_text("grid_detail_description")),
                ui.accordion_panel("Methods", ui.output_ui("grid_detail_method")),
                ui.accordion_panel("Geographic coverage and administrative level",ui.output_ui("grid_detail_geoadmin")),
                ui.accordion_panel("Collection dates and coverage",ui.output_ui("grid_detail_dates")),
                ui.accordion_panel("Themes and subjects",ui.output_ui("grid_detail_themes")),
                ui.accordion_panel("Further notes",ui.output_ui("grid_detail_further"))



            ),
            
            title="Details for selected resource",
            easy_close=True,
            footer=None,
        )
        ui.modal_show(m)

# download of a filtered csv
    @render.download(filename="output.csv")
    def download_filtered():
        data = grid_table.data_view()
        with io.BytesIO() as buf:
                data.to_csv(buf,header=True, index=False,encoding="utf-8")
                yield buf.getvalue() 

app = App(app_ui, server, static_assets=app_dir / "www")