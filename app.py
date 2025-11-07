import faicons as fa
import pandas as pd
import plotly.express as px
import numpy as np
from shared import app_dir, lgbtq, cv_resourceType, cv_producer, cv_themes, cv_subject, cv_country, cv_region, cv_adminLevel, cv_unitAnalysis,cv_longitudinal, cv_language, cv_restrictions

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
            "select_retype",
            "Select a Resource Type",
            cv_resourceType,
            selected="All"
        ),
        ui.input_selectize(
            "select_themes",
            "Select theme",
            cv_themes,
            multiple=False,
            selected="All"
        ),
        ui.input_selectize(
            "select_region",
            "Select region",
            cv_region,
            multiple=False,
            selected="All"
        ),
        ui.input_text("free_text", "Search for text", "Enter text..."),   
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
                              ui.output_data_frame("grid_table")
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
        
        # filter for Theme
        if input.select_themes() == "All":
            filt_themes = (lgbtq["Themes"] != "All") | (lgbtq["Themes"].isnull())
        else:
            filt_themes = (lgbtq["Themes"].notnull()) & (lgbtq["Themes"].str.contains(input.select_themes()))

        # filter for Region
        if input.select_region() == "All":
            filt_region = (lgbtq["GeographicRegion"] != "All") | (lgbtq["GeographicRegion"].isnull())
        else:
            filt_region = (lgbtq["GeographicRegion"].notnull()) & (lgbtq["GeographicRegion"].str.contains(input.select_region()))
        
        # free text input
        if input.free_text() == "Enter text...":
            filt_free = (lgbtq["GeographicRegion"] !="All") | (lgbtq["GeographicRegion"].isnull())
        else:
            filt_free = (lgbtq.apply(lambda row: row.astype(str).str.contains(input.free_text()).any(), axis=1))

        return lgbtq.loc[filt_resourcetype & filt_themes & filt_region & filt_free]

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


    @render.data_frame
    def grid_table():
        cols = ['Title', 'ResourceType', 'PubDate',
       'GeographicRegion','Language', 'Themes',
       'Subjects']
        
        return render.DataGrid(filtered_data()[cols], 
                                selection_mode="row", 
                                filters=True)

app = App(app_ui, server, static_assets=app_dir / "www")