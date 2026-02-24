import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
import numpy as np

# importar e transformar
# df = pd.read_csv('D:/Análises/Projeto Lotes/lotes_streamlit.csv')
df = pd.read_csv('lotes_streamlit_compactados.csv.gz')
df.drop(columns={'Unnamed: 0'}, inplace=True)

st.set_page_config(layout='wide')

# manter apenas a primeira ocorrência do lote
df = df.drop_duplicates(subset=['Lote'], keep='first')

df['Dt geração lote'] = pd.to_datetime(df['Dt geração lote'], dayfirst=True, format='mixed')
df['Data atendimento'] = pd.to_datetime(df['Data atendimento'], dayfirst=True, format='mixed')

df['Hora geração'] = pd.to_timedelta(df['Hora geração'])
df['Hora atendimento'] = pd.to_timedelta(df['Hora atendimento'])
df['Tempo atendimento'] = pd.to_timedelta(df['Tempo atendimento'])

df['Hora inteira geração'] = df['Hora inteira geração'].astype('Int64')
df['Hora inteira atendimento'] = df['Hora inteira atendimento'].astype('Int64')

# reordenar os meses
meses_ordenados = ['Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro', 'Janeiro', 'Fevereiro']
df['Mês atendimento'] = pd.Categorical(df['Mês atendimento'], categories=meses_ordenados, ordered=True)

# criar e ordenar os dias da semana
dias_semana = {
    'Monday': 'Segunda-Feira',
    'Tuesday': 'Terça-Feira',
    'Wednesday': 'Quarta-Feira',
    'Thursday': 'Quinta-Feira',
    'Friday': 'Sexta-Feira',
    'Saturday': 'Sábado',
    'Sunday': 'Domingo',
}
df['Dia semana'] = df['Data atendimento'].dt.day_name().map(dias_semana)
dias_semana_ordenado = ['Segunda-Feira', 'Terça-Feira', 'Quarta-Feira', 'Quinta-Feira', 'Sexta-Feira', 'Sábado', 'Domingo']
df['Dia semana'] = pd.Categorical(df['Dia semana'], categories=dias_semana_ordenado, ordered=True)

# transformar atendimentos sem turno
# lista de auxiliares com o problema de sem turno
lista_ax_semturno = df[df['Turno atendimento'] == 'Sem turno']['Usuário atend farmácia'].value_counts().reset_index(name='qtd')['Usuário atend farmácia'].tolist()

# para cada auxiliar, retorne o turno mais frequente de atendimento
for i in lista_ax_semturno:
    turnomaisfreq = df[df['Usuário atend farmácia'] == i]['Turno atendimento'].value_counts().reset_index(name='qtd').loc[0, 'Turno atendimento']
    
    # para cada auxiliar, adicione seu turno mais frequente onde ele não tinha turno
    df.loc[
        df['Turno atendimento'] == 'Sem turno',
        'Turno atendimento'
    ] = turnomaisfreq

########################################################################################################################################################################
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.title('Objetivo')
    st.write('Este relatório tem como objetivo analisar o comportamento da demanda das farmácias de internação do **5º** e **9º** andares de junho de 2025 a fevereiro de 2026, com foco na identificação de padrões temporais e possíveis horários de pico, a fim de apoiar decisões relacionadas à organização da equipe.')
    st.markdown('Os dados coletados abrangem o período de **31/06/2025** e **14/02/2026** das farmácias de internação do 5º e 9º andares.')

    st.header('Parte I: Demanda')
    st.subheader('Volume mensal')
    st.markdown('A quantidade de lotes atendidos pelas farmácias de internação do 5º e 9º andares vinha diminuindo gradativamente com o passar dos meses, algo que estava compatível com a sazonalidade das internações hospitalares. Esse padrão foi interrompido com a reabertura da Unidade de Internação 4º andar e a tarefa do 5º de assumir este novo setor. Em dezembro, a Farmácia 5º atendeu cerca de **8 mil** lotes (excluindo atendimentos em janela), número que saltou para **13 mil** em janeiro, um aumento superior a **60%**.')

    # gráfico mensal
    farmacia_mes = df.groupby('Farmácia')['Mês atendimento'].value_counts().reset_index(name='qtd').sort_values(by=['Farmácia', 'Mês atendimento'], ascending=[True, True])
    cores = ['#262A2E', "#D19D56", '#CC5A71'] #34344A

    gr_mes = px.line(
        farmacia_mes,
        x='Mês atendimento',
        y='qtd',
        # text='qtd',
        color='Farmácia',
        markers=True,
        title='A demanda mensal nas farmácias de internação',
        color_discrete_sequence=cores
    )

    gr_mes.update_yaxes(showticklabels=False, title_text='Quantidade de lotes', title_font=dict(color="#202020", weight='bold'))
    gr_mes.update_xaxes(
        tickfont=dict(color="#202020"),
        title_font=dict(color="#202020", weight='bold'),
        title_text='Mês de atendimento'
    )

    anotacoes = []
    for x, y, h in zip(farmacia_mes['Mês atendimento'], farmacia_mes['qtd'], farmacia_mes['Farmácia']):
        y_pos = y + 1000 if (x in ['Novembro', 'Dezembro'] and h == 'Farmácia 5º') else y + 300
        
        anotacoes.append(dict(
            x=x,
            y=y_pos,
            text=str(y),
            showarrow=False,
            font=dict(color="white", size=11, weight='bold'),
            bgcolor="#D19D56" if h == 'Farmácia 9º' else "#202020",
            opacity=0.9,
            borderpad=2,
            borderwidth=1,
            bordercolor="#202020",
            align='center'
        ))

    gr_mes.update_layout(annotations=anotacoes, yaxis=dict(showgrid=True))

    st.write(gr_mes)

    st.markdown('Se olharmos rapidamente, entenderemos que a Unidade de Internação 4º andar aumentou em **60%** a quantidade de lotes atendidos por mês na Farmácia 5º, mas os números são diferentes do que aparentam. **Dos 13 mil lotes atendidos em janeiro, 3.721 (29%) eram, de fato, do 4º andar**. O restante está distribuído em cerca de **4.690 (36%)** para a UI 5º e **4.580 (35%)** para a UI 6º.')
    st.markdown('Essa informação mostra que assumir um setor novo explica **parte do aumento** na demanda do 5º andar, **mas não sua totalidade**, ou seja, mesmo desconsiderando os atendimentos da UI 4º andar, é possível notar um aumento no volume total da Farmácia 5º.')

########################################################################################################################################################################
    st.subheader('Volume diário')
    st.markdown('O número médio de lotes atendidos por dia na Farmácia Internação 5º andar passou de **252** em dezembro para **324** em janeiro, um aumento de pouco mais de **90 lotes (36%)** por dia, o que faz com que a Farmácia 5º atenda, em média, cerca de 100 lotes a mais por dia que a farmácia do 9º.')

    # quantidade média de lotes por mês com o passar dos meses
    mediadiariames_farmacia = df.groupby(['Farmácia', 'Mês atendimento', 'Data atendimento']).size().reset_index(name='qtd')
    media_diaria_por_mes = (
        mediadiariames_farmacia[mediadiariames_farmacia['qtd'] > 0] 
        .groupby(['Farmácia', 'Mês atendimento'])['qtd']
        .mean()
        .reset_index(name='media_diaria')
    )

    gr_dia = px.line(
        media_diaria_por_mes,
        x='Mês atendimento',
        y='media_diaria',
        # text='media_diaria',
        color='Farmácia',
        markers=True,
        title='Demanda diária nas farmácias de internação',
        color_discrete_sequence=cores
    )

    gr_dia.update_yaxes(showticklabels=False, title_text='Quantidade de lotes', title_font=dict(color="#202020", weight='bold'))
    gr_dia.update_xaxes(
        tickfont=dict(color="#202020"),
        title_font=dict(color="#202020", weight='bold'),
        title_text='Mês de atendimento'
    )

    anotacoes = []
    for x, y, h in zip(media_diaria_por_mes['Mês atendimento'], media_diaria_por_mes['media_diaria'].round().astype(int), media_diaria_por_mes['Farmácia']):
        # Sua lógica de offset
        y_pos = y + 26 if (x in ['Novembro', 'Dezembro'] and h == 'Farmácia 5º') else y
        # y_pos = y
        
        anotacoes.append(dict(
            x=x,
            y=y_pos,
            text=str(y),
            showarrow=False,
            font=dict(color="white", size=11, weight='bold'),
            bgcolor="#D19D56" if h == 'Farmácia 9º' else "#202020", # O facecolor que você pediu
            opacity=0.9,       # O alpha
            borderpad=2,       # O pad
            borderwidth=1,      # Pode adicionar borda se quiser
            bordercolor="#202020",
            align='center'
        ))

    gr_dia.update_layout(annotations=anotacoes, yaxis=dict(showgrid=True))
    st.write(gr_dia)
    
    st.markdown('Com a incorporação da Unidade de Internação do 4º andar e o aumento da demanda das UI 5º e 6º, a Farmácia 5º passou a atender volume significativamente maior de lotes, sobretudo no turno da noite, onde a quantidade média de lotes aumentou **78%** em apenas um mês.')
########################################################################################################################################################################
    # media de lotes por dia por cada turno | farmácia 5º
    turno_abs = df[
        (df['Farmácia'] == 'Farmácia 5º')
    ].groupby(['Mês atendimento','Data atendimento', 'Turno atendimento']).size().reset_index(name='qtd')

    turno_media = turno_abs[turno_abs['qtd'] > 0].groupby(['Mês atendimento', 'Turno atendimento'])['qtd'].mean().reset_index()

    gr_turno = px.line(
        turno_media,
        x='Mês atendimento',
        y='qtd',
        color='Turno atendimento',
        markers=True,
        color_discrete_sequence=cores
    )

    gr_turno.update_yaxes(showticklabels=True, title_text='Quantidade de lotes', title_font=dict(color="#202020", weight='bold'))
    gr_turno.update_xaxes(
        tickfont=dict(color="#202020"),
        title_font=dict(color="#202020", weight='bold'),
        title_text='Mês de atendimento'
    )
    
    meses_rotulos = ['Julho', 'Janeiro', 'Dezembro']
    anotacoes_turno = []
    for x, y, h in zip(turno_media['Mês atendimento'], turno_media['qtd'].round().astype(int), turno_media['Turno atendimento']):
        # Sua lógica de offset
        y_pos = y + 20 if (x in ['Dezembro'] and h == 'Tarde') else y + 10 if (x in ['Dezembro'] and h == 'Noite') else y
        # y_pos = y
        
        if str(x) in meses_rotulos:
            anotacoes_turno.append(dict(
                x=x,
                y=y_pos,
                text=str(y),
                showarrow=False,
                font=dict(color="white", size=11, weight='bold'),
                bgcolor="#D19D56" if h == 'Noite' else"#CC5A71" if h == 'Tarde' else "#202020",
                opacity=0.9,       
                borderpad=2,       
                borderwidth=0,
                bordercolor="#202020",
                align='center'
            ))
    gr_turno.update_layout(
        annotations=anotacoes_turno,
        title=dict(
            text="Quantidade média de lotes por turno",
            subtitle=dict(
                text="Distribuição por mês na <b>Farmácia 5º</b>",
                font=dict(
                    size=14,
                ),
            )
        ),
        margin=dict(t=80, l=50, r=50, b=50)
    )
    
    gr_turno.update_layout(annotations=anotacoes_turno)
    st.write(gr_turno)
    
    # media de lotes por dia por cada turno | farmácia 5º
    turno_abs9 = df[
        (df['Farmácia'] == 'Farmácia 9º')
    ].groupby(['Mês atendimento','Data atendimento', 'Turno atendimento']).size().reset_index(name='qtd')

    turno_media9 = turno_abs9[turno_abs9['qtd'] > 0].groupby(['Mês atendimento', 'Turno atendimento'])['qtd'].mean().reset_index()
    
    gr_turno9 = px.line(
        turno_media9,
        x='Mês atendimento',
        y='qtd',
        color='Turno atendimento',
        markers=True,
        color_discrete_sequence=cores
    )

    gr_turno9.update_yaxes(showticklabels=True, title_text='Quantidade de lotes', title_font=dict(color="#202020", weight='bold'))
    gr_turno9.update_xaxes(
        tickfont=dict(color="#202020"),
        title_font=dict(color="#202020", weight='bold'),
        title_text='Mês de atendimento'
    )
    
    meses_rotulos = ['Julho', 'Janeiro', 'Dezembro']
    anotacoes_turno9 = []
    for x, y, h in zip(turno_media9['Mês atendimento'], turno_media9['qtd'].round().astype(int), turno_media9['Turno atendimento']):
        # y_pos = y + 20 if (x in ['Dezembro'] and h == 'Tarde') else y + 10 if (x in ['Dezembro'] and h == 'Noite') else y
        y_pos = y
        
        if str(x) in meses_rotulos:
            anotacoes_turno9.append(dict(
                x=x,
                y=y_pos,
                text=str(y),
                showarrow=False,
                font=dict(color="white", size=11, weight='bold'),
                bgcolor="#D19D56" if h == 'Noite' else"#CC5A71" if h == 'Tarde' else "#202020",
                opacity=0.9,
                borderpad=2,
                borderwidth=0,
                bordercolor="#202020",
                align='center'
            ))
    gr_turno9.update_layout(
        annotations=anotacoes_turno9,
        title=dict(
            text="Quantidade média de lotes por turno",
            subtitle=dict(
                text="Distribuição por mês na <b>Farmácia 9º</b>",
                font=dict(
                    size=14,
                ),
            )
        ),
        margin=dict(t=80, l=50, r=50, b=50)
    )
    st.write(gr_turno9)
########################################################################################################################################################################
    st.subheader('Horários de pico')
    st.markdown('A concentração na quantidade de lotes por hora era algo relevante antes mesmo da entrada da UI 4º, mas se tornou ainda mais impactante após a mudança e aumento geral da demanda. Tanto a Farmácia 5º quanto a Farmácia 9º possuem uma concentração de atendimentos às **0h**, **16h** e **23h**. Em janeiro, porém, os números aumentaram bastante, especialmente durante a noite.')
    st.markdown('Neste primeiro momento já podemos notar que a Farmácia 9º possui **três horários de pico** com quantidades semelhantes de lote, na média entre 16 e 22. Algo bem diferente da Farmácia 5º, onde a maior quantidade de atendimentos está concentrada no turno da noite, entre 23h e 1h, quando eles atendem, em média, **o dobro** do que se atende às 16h.')
    
    opcoes_meses = df['Mês atendimento'].unique()
    mes_selecionado = st.pills('Selecione o mês para filtrar', opcoes_meses, selection_mode='single', default='Janeiro')
    mes_selecionado = [mes_selecionado]
    
    # média por hora farmácia 5º
    lotes_por_hora_dia5 = (
        df[
            (df['Farmácia'] == 'Farmácia 5º') &
            (df['Mês atendimento'].isin(mes_selecionado))
        ]
        .groupby(['Data atendimento', 'Hora inteira atendimento'])
        .size()
        .reset_index(name='qtd_lotes')
    )

    media_por_hora5 = (
        lotes_por_hora_dia5
        .groupby('Hora inteira atendimento')['qtd_lotes']
        .mean()
        .reset_index()
    )
    
    # média por hora farmácia 9º
    lotes_por_hora_dia9 = (
        df[
            (df['Farmácia'] == 'Farmácia 9º') &
            (df['Mês atendimento'].isin(mes_selecionado))
        ]
        .groupby(['Data atendimento', 'Hora inteira atendimento'])
        .size()
        .reset_index(name='qtd_lotes')
    )

    media_por_hora9 = (
        lotes_por_hora_dia9
        .groupby('Hora inteira atendimento')['qtd_lotes']
        .mean()
        .reset_index()
    )

    # média por hora farmácia 5º sem o 4º andar
    setores4 = ['Unidade de Internação  4º andar', 'Unidade de Cuidados Intermediários - UCI 4° Andar']
    lotes_por_hora_dia4 = (
        df[
            (df['Farmácia'] == 'Farmácia 5º') &
            (~df['Setor de atendimento'].isin(setores4)) &
            (df['Mês atendimento'].isin(mes_selecionado))
        ]
        .groupby(['Data atendimento', 'Hora inteira atendimento'])
        .size()
        .reset_index(name='qtd_lotes')
    )

    media_por_hora4 = (
        lotes_por_hora_dia4
        .groupby('Hora inteira atendimento')['qtd_lotes']
        .mean()
        .reset_index()
    )

    # agrupar o 5º sem e com o 4º andar
    mediahora5comesem4 = pd.merge(media_por_hora5, media_por_hora4, on='Hora inteira atendimento')

    mediahora5comesem4e9 = pd.merge(mediahora5comesem4, media_por_hora9, on='Hora inteira atendimento')
    
    # derreter as colunas para ficarem juntas
    df_5com4e9 = mediahora5comesem4e9.melt(
        id_vars=['Hora inteira atendimento'],
        value_vars=['qtd_lotes_x', 'qtd_lotes_y', 'qtd_lotes'],
        var_name='Periodo',
        value_name='media_hora'
    )

    df_5com4e9['Periodo'] = df_5com4e9['Periodo'].map({
        'qtd_lotes_x': 'Farmácia 5º com 4º andar',
        'qtd_lotes_y': 'Farmácia 5º sem 4º andar',
        'qtd_lotes': 'Farmácia 9º'
    })
    
    gr_hora = px.line(
        df_5com4e9,
        x='Hora inteira atendimento',
        y='media_hora',
        color='Periodo',
        markers=True,
        color_discrete_sequence=cores
    )

    gr_hora.update_yaxes(showticklabels=True, title_text='Quantidade de lotes', title_font=dict(color="#202020", weight='bold'))
    gr_hora.update_xaxes(
        tickfont=dict(color="#202020"),
        title_font=dict(color="#202020", weight='bold'),
        title_text='Horários'
    )
    
    anotacoes_hora = []
    for x, y, h in zip(df_5com4e9['Hora inteira atendimento'], df_5com4e9['media_hora'].round().astype(int), df_5com4e9['Periodo']):
        # y_pos = y + 4 if (x == 16 and h == 'Farmácia 5º com 4º andar') else y
        y_pos = y
        
        if x in [0, 16, 23]:
            anotacoes_hora.append(dict(
                x=x,
                y=y_pos,
                text=str(y),
                showarrow=False,
                font=dict(color="white", size=11, weight='bold'),
                bgcolor="#D19D56" if h == 'Farmácia 5º sem 4º andar' else"#CC5A71" if h == 'Farmácia 9º' else "#202020",
                opacity=0.9,       
                borderpad=2,       
                borderwidth=0,
                bordercolor="#202020",
                align='center'
            ))
    
    gr_hora.update_layout(
        annotations=anotacoes_hora,
        title=dict(
            text="Horários de pico nas farmácias de internação",
            subtitle=dict(
                text="Quantidade média de lotes por hora",
                font=dict(
                    size=14,
                ),
            )
        ),
        margin=dict(t=80, l=50, r=50, b=50)
    )
    st.write(gr_hora)
    
    st.markdown('Em dezembro, houve uma concentração de **81** lotes em média atendidos entre as 23h e 1h na Farmácia 5º, em janeiro essa concentração passou para **141**, o **maior pico de atendimento entre as farmácias**.')
    st.markdown('Entender os horários de maior demanda permite uma melhor organização de escala, intervalos e uma possível ajuda entre farmácias. Tanto a Farmácia 5º quanto a Farmácia 9º dividem os mesmos horários de pico, com especial concentração no início das noites do 5º. Isto é um reflexo do horário em que os lotes são majoritariamente prescritos e/ou gerados, **entre 9h e 14h**. Além disso, apesar de a farmácia do 5º andar possuir uma grande quantidade de lotes, precisamos levar também em consideração os atendimentos em janela e espaço físico, algo que poderia limitar a ajuda que o 5º recebe.')
########################################################################################################################################################################
    st.header('Parte II: Capacidade')
    st.subheader('Lotes por auxiliar')
    st.markdown('Em novembro e dezembro, os auxiliares da Farmácia 5º atenderam, em média, **24** e **29** lotes por plantão noturno, respectivamente. Em janeiro, esse número saltou para **52 lotes por auxiliar**. Considerando escalas com apenas dois auxiliares no turno, a carga individual pode alcançar aproximadamente **104 lotes** por profissional.')
    
    turno_media['qtd_tres_ax'] = turno_media['qtd'] / 3
    
    gr_media_ax = px.line(
        turno_media,
        x='Mês atendimento',
        y='qtd_tres_ax',
        color='Turno atendimento',
        markers=True,
        color_discrete_sequence=cores
    )

    gr_media_ax.update_yaxes(showticklabels=True, title_text='Quantidade de lotes', title_font=dict(color="#202020", weight='bold'))
    gr_media_ax.update_xaxes(
        tickfont=dict(color="#202020"),
        title_font=dict(color="#202020", weight='bold'),
        title_text='Mês de atendimento'
    )
    
    anotacoes_media_ax = []
    for x, y, h in zip(turno_media['Mês atendimento'], turno_media['qtd_tres_ax'].round().astype(int), turno_media['Turno atendimento']):
        # y_pos = y + 4 if (x == 16 and h == 'Farmácia 5º com 4º andar') else y
        y_pos = y
        
        if x in ['Julho', 'Novembro', 'Dezembro', 'Janeiro']:
            anotacoes_media_ax.append(dict(
                x=x,
                y=y_pos,
                text=str(y),
                showarrow=False,
                font=dict(color="white", size=11, weight='bold'),
                bgcolor= "#D19D56" if h == 'Noite' else"#CC5A71" if h == 'Tarde' else "#202020",
                opacity=0.9,       
                borderpad=2,       
                borderwidth=0,
                bordercolor="#202020",
                align='center'
            ))
    
    gr_media_ax.update_layout(
        annotations=anotacoes_media_ax,
        title=dict(
            text="A demanda de cada auxiliar na Farmácia 5º",
            subtitle=dict(
                text="Quantidade média de lotes por auxiliar | <b>3 auxiliares por turno</b>",
                font=dict(
                    size=14,
                ),
            )
        ),
        margin=dict(t=80, l=50, r=50, b=50)
    )
    st.write(gr_media_ax)
    
    # média dos auxiliares farmácia 9º

    turno_media9['qtd_dois_ax'] = turno_media9['qtd'] / 2
    
    gr_media_ax9 = px.line(
        turno_media9,
        x='Mês atendimento',
        y='qtd_dois_ax',
        color='Turno atendimento',
        markers=True,
        color_discrete_sequence=cores
    )

    gr_media_ax9.update_yaxes(showticklabels=True, title_text='Quantidade de lotes', title_font=dict(color="#202020", weight='bold'))
    gr_media_ax9.update_xaxes(
        tickfont=dict(color="#202020"),
        title_font=dict(color="#202020", weight='bold'),
        title_text='Mês de atendimento'
    )
    
    anotacoes_media_ax9 = []
    for x, y, h in zip(turno_media9['Mês atendimento'], turno_media9['qtd_dois_ax'].round().astype(int), turno_media9['Turno atendimento']):
        # y_pos = y + 4 if (x == 16 and h == 'Farmácia 5º com 4º andar') else y
        y_pos = y
        
        if x in ['Julho', 'Novembro', 'Dezembro', 'Janeiro']:
            anotacoes_media_ax9.append(dict(
                x=x,
                y=y_pos,
                text=str(y),
                showarrow=False,
                font=dict(color="white", size=11, weight='bold'),
                bgcolor= "#D19D56" if h == 'Noite' else"#CC5A71" if h == 'Tarde' else "#202020",
                opacity=0.9,       
                borderpad=2,       
                borderwidth=0,
                bordercolor="#202020",
                align='center'
            ))
    
    gr_media_ax9.update_layout(
        annotations=anotacoes_media_ax9,
        title=dict(
            text="A demanda de cada auxiliar na Farmácia 9º",
            subtitle=dict(
                text="Quantidade média de lotes por auxiliar | <b>2 auxiliares por turno</b>",
                font=dict(
                    size=14,
                ),
            )
        ),
        margin=dict(t=80, l=50, r=50, b=50)
    )
    st.write(gr_media_ax9)
    
    st.markdown('Com estes gráficos podemos notar que, durante o dia, a demanda na Farmácia 9º é maior para **cada um** dos dois auxiliares do que na Farmácia 5º entre três, mesmo que, em números totais, a Farmácia 5º ainda se sobressaia.')
    st.markdown('Isto significa que qualquer farmácia com um funcionário ausente será prejudicada. A demanda no 9º é menor; a quantidade de auxiliares também.')
########################################################################################################################################################################
    st.subheader('Tempo de cada atendimento')
    st.markdown('Ao considerarmos o tempo necessário para atendimento de cada lote, surgem informações relevantes sobre a carga de trabalho das equipes.')
    st.markdown('Na Farmácia 5º, **90%** dos lotes são concluídos em até **2 minutos e 47 segundos**, enquanto **75%** são finalizados em até **1 minuto e 15 segundos**, evidenciando agilidade no processo.')
    st.markdown('Em dezembro, a equipe da tarde atendeu, em média, **90 lotes** por dia, com tempo médio de **1 minuto e 56 segundos por lote**, totalizando aproximadamente **2 horas e 55 minutos** dedicadas exclusivamente ao atendimento de lotes.')
    st.markdown('Em janeiro, o tempo médio por lote aumentou para **2 minutos e 4 segundos**, o que, aliado ao maior volume de atendimentos, resultou em cerca de **4 horas** de trabalho direcionado apenas a essa atividade.')

    media_turno = df[
    (df['Tempo atendimento'] < pd.to_timedelta('00:10:00')) &
    (df['Farmácia'] == 'Farmácia 5º')
    ].groupby(['Mês atendimento', 'Turno atendimento'])['Tempo atendimento'].mean().reset_index(name='media')

    media_turno['tempo_total_seg'] = media_turno['media'] * turno_media['qtd']

    media_turno['tempo_timedelta'] = pd.to_timedelta(
        media_turno['tempo_total_seg'], unit='s'
    )

    media_turno['tempo_formatado'] = (
        media_turno['tempo_timedelta']
        .dt.components['hours'].astype(str) + 'h ' +
        media_turno['tempo_timedelta']
        .dt.components['minutes'].astype(str) + 'min'
    )

    media_turno['inteiro'] = media_turno['tempo_total_seg'].astype(int)
    media_turno = media_turno.reset_index()
    
    gr_tempo = px.line(
        media_turno,
        x='Mês atendimento',
        y='inteiro',
        color='Turno atendimento',
        markers=True,
        color_discrete_sequence=cores
    )

    gr_tempo.update_yaxes(showticklabels=False, title_text='Tempo dedicado', title_font=dict(color="#202020", weight='bold'))
    gr_tempo.update_xaxes(
        tickfont=dict(color="#202020"),
        title_font=dict(color="#202020", weight='bold'),
        title_text='Mês de atendimento'
    )
    
    anotacoes_tempo = []
    for x, y, t, t2 in zip(media_turno['Mês atendimento'], media_turno['inteiro'].round().astype(int), media_turno['tempo_formatado'], media_turno['Turno atendimento']):
        # y_pos = y + 4 if (x == 16 and h == 'Farmácia 5º com 4º andar') else y
        y_pos = y
        
        if x in ['Julho', 'Novembro', 'Dezembro', 'Janeiro']:
            anotacoes_tempo.append(dict(
                x=x,
                y=y_pos,
                text=str(t),
                showarrow=False,
                font=dict(color="white", size=11, weight='bold'),
                bgcolor= "#D19D56" if t2 == 'Noite' else"#CC5A71" if t2 == 'Tarde' else "#202020",
                opacity=0.9,       
                borderpad=2,       
                borderwidth=0,
                bordercolor="#202020",
                align='center'
            ))
    
    gr_tempo.update_layout(
        annotations=anotacoes_tempo,
        title=dict(
            text="O turno da tarde aumentou em mais de uma hora seu tempo de atendimento",
            subtitle=dict(
                text="Tempo médio dedicado exclusivamente ao atendimento de lotes por turno | <b>Farmácia 5º</b>",
                font=dict(
                    size=14,
                ),
            )
        ),
        margin=dict(t=80, l=50, r=50, b=50)
    )
    st.write(gr_tempo)
    
    # média turno farmácia 9º
    media_turno9 = df[
    (df['Tempo atendimento'] < pd.to_timedelta('00:10:00')) &
    (df['Farmácia'] == 'Farmácia 9º')
    ].groupby(['Mês atendimento', 'Turno atendimento'])['Tempo atendimento'].mean().reset_index(name='media')

    media_turno9['tempo_total_seg'] = media_turno9['media'] * turno_media['qtd']

    media_turno9['tempo_timedelta'] = pd.to_timedelta(
        media_turno9['tempo_total_seg'], unit='s'
    )

    media_turno9['tempo_formatado'] = (
        media_turno9['tempo_timedelta']
        .dt.components['hours'].astype(str) + 'h ' +
        media_turno9['tempo_timedelta']
        .dt.components['minutes'].astype(str) + 'min'
    )

    media_turno9['inteiro'] = media_turno9['tempo_total_seg'].astype(int)
    media_turno9 = media_turno9.reset_index()
    
    gr_tempo9 = px.line(
        media_turno9,
        x='Mês atendimento',
        y='inteiro',
        color='Turno atendimento',
        markers=True,
        color_discrete_sequence=cores
    )

    gr_tempo9.update_yaxes(showticklabels=False, title_text='Tempo dedicado', title_font=dict(color="#202020", weight='bold'))
    gr_tempo9.update_xaxes(
        tickfont=dict(color="#202020"),
        title_font=dict(color="#202020", weight='bold'),
        title_text='Mês de atendimento'
    )
    
    anotacoes_tempo = []
    for x, y, t, t2 in zip(media_turno9['Mês atendimento'], media_turno9['inteiro'].round().astype(int), media_turno9['tempo_formatado'], media_turno9['Turno atendimento']):
        # y_pos = y + 4 if (x == 16 and h == 'Farmácia 5º com 4º andar') else y
        y_pos = y
        
        if x in ['Julho', 'Novembro', 'Dezembro', 'Janeiro']:
            anotacoes_tempo.append(dict(
                x=x,
                y=y_pos,
                text=str(t),
                showarrow=False,
                font=dict(color="white", size=11, weight='bold'),
                bgcolor= "#D19D56" if t2 == 'Noite' else"#CC5A71" if t2 == 'Tarde' else "#202020",
                opacity=0.9,       
                borderpad=2,       
                borderwidth=0,
                bordercolor="#202020",
                align='center'
            ))
    
    gr_tempo9.update_layout(
        annotations=anotacoes_tempo,
        title=dict(
            text="A Farmácia 9º acompanhou a demanda do 5º em janeiro",
            subtitle=dict(
                text="Tempo médio dedicado exclusivamente ao atendimento de lotes por turno | <b>Farmácia 9º</b>",
                font=dict(
                    size=14,
                ),
            )
        ),
        margin=dict(t=80, l=50, r=50, b=50)
    )
    st.write(gr_tempo9)
    
    st.markdown('Apesar de a quantidade de lotes da Farmácia 9º ter diminuído de dezembro para janeiro - ao passo que no 5º aumentou -, é possível notar um aumento no tempo dedicado aos lotes com o passar destes meses, seja por aumento na complexidade de cada atendimento, trocas e/ou empréstimos de funcionários ou outras demandas que influenciem a conclusão da tarefa. Isto significa que a Farmácia 9º, em janeiro, acompanhou de perto a demanda/complexidade da Farmácia 5º.')
########################################################################################################################################################################
    st.header('Parte III: Eficiência')
    st.subheader('Percentual do turno ocupado')
    
    tempo_dedicado = st.number_input('Insira em horas o tempo deve ser dedicado aos lotes por turno', min_value=1, max_value=7, step=1, value=4)
    st.caption('Entre 1 e 7 horas.')
    pcr_tempo_dedicado = round((tempo_dedicado / 7) * 100)
    restante_tempo = 7 - tempo_dedicado
    
    st.markdown(f'Vamos estipular um cenário onde, das sete horas disponíveis por turno, o auxiliar deva dedicar **até {tempo_dedicado} horas** (~{pcr_tempo_dedicado}% do turno) para o atendimento de lotes. Dessa forma, o auxiliar terá **{restante_tempo} horas** restantes para a conclusão de outras tarefas, como contagem de curvas, recebimento e/ou solicitação de materiais e medicamentos, organização da farmácia, dentre outras tarefas pertinentes.')
    st.markdown('Com este cenário em mente, vamos considerar o seguinte: se uma equipe dedicou até 60% do tempo atendendo lotes, o turno foi concluído com **folga**; entre 60% e 80% do tempo, o turno foi **saudável**; entre 80% e 95%, é preciso **atenção** e, mais de 95%, o turno teve uma **sobrecarga**, onde os auxiliares não conseguiram concluir as tarefas ou chegaram ao limite de sua capacidade.')
    
    saude_atendimento = pd.DataFrame({
        'Folga': '🆗 <60%',
        'Saudável': '✅ 60-80%',
        'Atenção': '⚠️ 80-95%',
        'Sobrecarga': '❌ 95%>',
    }, index=[0])
    
    st.dataframe(saude_atendimento, hide_index=True)

    media_turno['hora_inteira'] = (media_turno['tempo_timedelta'].dt.total_seconds() / 3600)
    media_turno['dedicacao'] = round((media_turno['hora_inteira'] / tempo_dedicado) * 100)

    media_turno9['hora_inteira'] = (media_turno9['tempo_timedelta'].dt.total_seconds() / 3600)
    media_turno9['dedicacao'] = round((media_turno9['hora_inteira'] / tempo_dedicado) * 100)
    
    gr_ocupacao_tempo = px.line(
        media_turno,
        x='Mês atendimento',
        y='dedicacao',
        color='Turno atendimento',
        markers=True,
        color_discrete_sequence=cores
    )

    gr_ocupacao_tempo.update_yaxes(showticklabels=True, title_text='Tempo dedicado (%)', title_font=dict(color="#202020", weight='bold'))
    gr_ocupacao_tempo.update_xaxes(
        tickfont=dict(color="#202020"),
        title_font=dict(color="#202020", weight='bold'),
        title_text='Mês de atendimento'
    )
    
    anotacoes_ocupacao = []
    for x, y, t, t2 in zip(media_turno['Mês atendimento'], media_turno['dedicacao'].round(), media_turno['dedicacao'].astype(int), media_turno['Turno atendimento']):
        # y_pos = y + 4 if (x == 16 and h == 'Farmácia 5º com 4º andar') else y
        y_pos = y
        
        if x in ['Julho', 'Novembro', 'Dezembro', 'Janeiro']:
            anotacoes_ocupacao.append(dict(
                x=x,
                y=y_pos,
                text=str(f'{t}%'),
                showarrow=False,
                font=dict(color="white", size=11, weight='bold'),
                bgcolor= "#D19D56" if t2 == 'Noite' else"#CC5A71" if t2 == 'Tarde' else "#202020",
                opacity=0.9,       
                borderpad=2,       
                borderwidth=0,
                bordercolor="#202020",
                align='center'
            ))
    
    gr_ocupacao_tempo.update_layout(
        annotations=anotacoes_ocupacao,
        title=dict(
            text="Um aumento claro de demanda durante a tarde em janeiro",
            subtitle=dict(
                text="Parte do turno dedicada ao atendimento de lotes | <b>Farmácia 5º</b>",
                font=dict(
                    size=14,
                ),
            )
        ),
        margin=dict(t=80, l=50, r=50, b=50)
    )
    
    
    # Zona de folga (0–60)
    gr_ocupacao_tempo.add_hrect(
        y0=0,
        y1=60,
        fillcolor="lightblue",
        opacity=0.08,
        line_width=0
    )
    
    # Zona saudável (0–0.7)
    gr_ocupacao_tempo.add_hrect(
        y0=60,
        y1=80,
        fillcolor="green",
        opacity=0.08,
        line_width=0
    )
    

    # Zona de atenção (0.7–0.85)
    gr_ocupacao_tempo.add_hrect(
        y0=80,
        y1=95,
        fillcolor="yellow",
        opacity=0.08,
        line_width=0
    )

    # Zona de sobrecarga (>0.85)
    gr_ocupacao_tempo.add_hrect(
        y0=95,
        y1=102,
        fillcolor="red",
        opacity=0.08,
        line_width=0
    )
    st.write(gr_ocupacao_tempo)

    # ocupação do tempo 9º
    gr_ocupacao_tempo9 = px.line(
        media_turno9,
        x='Mês atendimento',
        y='dedicacao',
        color='Turno atendimento',
        markers=True,
        color_discrete_sequence=cores
    )

    gr_ocupacao_tempo9.update_yaxes(showticklabels=True, title_text='Parte do turno (%)', title_font=dict(color="#202020", weight='bold'))
    gr_ocupacao_tempo9.update_xaxes(
        tickfont=dict(color="#202020"),
        title_font=dict(color="#202020", weight='bold'),
        title_text='Mês de atendimento'
    )
    
    anotacoes_ocupacao9 = []
    for x, y, t, t2 in zip(media_turno9['Mês atendimento'], media_turno9['dedicacao'].round(), media_turno9['dedicacao'].astype(int), media_turno9['Turno atendimento']):
        # y_pos = y + 4 if (x == 16 and h == 'Farmácia 5º com 4º andar') else y
        y_pos = y
        
        if x in ['Julho', 'Novembro', 'Dezembro', 'Janeiro']:
            anotacoes_ocupacao9.append(dict(
                x=x,
                y=y_pos,
                text=str(f'{t}%'),
                showarrow=False,
                font=dict(color="white", size=11, weight='bold'),
                bgcolor= "#D19D56" if t2 == 'Noite' else"#CC5A71" if t2 == 'Tarde' else "#202020",
                opacity=0.9,       
                borderpad=2,       
                borderwidth=0,
                bordercolor="#202020",
                align='center'
            ))
    
    gr_ocupacao_tempo9.update_layout(
        annotations=anotacoes_ocupacao9,
        title=dict(
            text="Um aumento claro de demanda durante a tarde em janeiro",
            subtitle=dict(
                text="Parte do turno dedicada ao atendimento de lotes | <b>Farmácia 9º</b>",
                font=dict(
                    size=14,
                ),
            )
        ),
        margin=dict(t=80, l=50, r=50, b=50)
    )
    
    
    # Zona de folga (0–60)
    gr_ocupacao_tempo9.add_hrect(
        y0=0,
        y1=60,
        fillcolor="lightblue",
        opacity=0.08,
        line_width=0
    )
    
    # Zona saudável (0–0.7)
    gr_ocupacao_tempo9.add_hrect(
        y0=60,
        y1=80,
        fillcolor="green",
        opacity=0.08,
        line_width=0
    )
    

    # Zona de atenção (0.7–0.85)
    gr_ocupacao_tempo9.add_hrect(
        y0=80,
        y1=95,
        fillcolor="yellow",
        opacity=0.08,
        line_width=0
    )

    # Zona de sobrecarga (>0.85)
    gr_ocupacao_tempo9.add_hrect(
        y0=95,
        y1=102,
        fillcolor="red",
        opacity=0.08,
        line_width=0
    )
    st.write(gr_ocupacao_tempo9)
    
    st.markdown('É possível notar uma clara sobrecarga/alerta no período da tarde em janeiro em ambas farmácias de internação. O que antes foi um turno saudável por meses, se tortou o turno mais intenso, não apenas no 5º andar, onde as mudanças foram mais claras, mas também no 9º.')
    st.markdown('Essa mudança brusca na intensidade dos atendimentos, tanto em quantidade quanto complexidade, explica as solicitações de auxílio que as farmácias 5º e 9º fazem. Ambas farmácias mantiveram turnos saudáveis por meses, mesmo com a alta demanda no inverno, mas o aumento na quantidade e complexidade de lotes, troca de auxiliares e mudanças de processos trouxeram números que as equipes não estavam preparadas para lidar.')
    
    st.header('Part IV: Conclusão')
    st.subheader('A demanda aumentou?')
    st.markdown('Sim, a demanda definitivamente aumentou. No entanto, apenas parte do aumento na quantidade de lotes tanto na Farmácia 5º quanto na Farmácia 9º foi fruto da mudança envolvendo a UI 4º andar.')
    st.markdown('Na Farmácia 5º, assumir a UI 4º andar aumentou a quantidade de lotes em números absolutos no turno da noite e a complexidade no turno da tarde. Com mais atendimentos em janela, lotes na tela e um estoque maior para administrar - mesmo em um espaço pequeno -, a Farmácia 5º sentiu a mudança já no primeiro mês, mesmo herdando auxiliares da Farmácia 3º.')
    st.markdown('Além disso, foi possível notar que a Farmácia 9º está acompanhando de perto a demanda do 5º andar, especialmente o turno da tarde, onde ambas farmácias beiram a margem de atenção, às vezes atingindo a sobrecarga.')
    
    st.subheader('A eficiência mudou?')
    st.markdown('Sim, o tempo médio de atendimento de lotes aumentou em ambas farmácias, sendo este um resultado do aumento na quantidade de lotes e um possível desgaste nos auxiliares, maior complexidade dos lotes e/ou sistema ou, também, equipe nova ainda em treinamento, sendo contratação ou troca de farmácia. Uma segunda análise ao fim de fevereiro pode definir os motivos da mudança de eficiência.')
    
    st.subheader('Os turnos estão sobrecarregados?')
    st.markdown('A mudança de demanda afetou todos os turnos nas duas farmácias, com especial destaque para o **turno da noite na Farmácia 5º** e o **turno da tarde em ambas farmácias**.')
    st.markdown('O turno da noite do 5º, apesar de ter absorvido a maior quantidade de lotes, está lidando bem com a nova demanda, muito possivelmente por ter herdado, também, novos auxiliares da Farmácia 3º. Com uma boa organização, a equipe se mantém em um ritmo saudável quando possui três auxiliares, o que mantém a demanda em 50 lotes para cada um - algo parecido com a Farmácia 9º - e possibilita o adiantamento de lotes.')
    st.markdown('Por outro lado, o turno da tarde em ambas farmácias, foi surpreendido com a nova demanda e pulou de um :green[**ritmo saudável**] para um :red[**estado de alerta**]. O auxílio vindo do turno da noite - quando possível, apesar da alta demanda -, do turno da manhã e/ou de outras farmácias pode se fazer necessário nesse primeiro período de adaptação.')
    
    st.subheader('Existe risco operacional?')
    st.markdown('As equipes possuem outras tarefas além do atendimento de lotes: atendimento de janela, contagem de curvas, organização, intervalos de outras equipes, dentre outras. Quando o atendimento de lotes ocupa grande parte - senão todo - tempo disponível, isso faz com que a equipe não consiga concluir atividades como contagem de curvas e recebimento/solicitação de materiais/medicamentos, o que afeta diariamente a acuracidade do estoque. Uma baixa acuracidade gera maior demanda e falta de confiança no que de fato há disponível no estoque.')
    st.markdown('Esses problemas, se não forem resolvidos, podem, sim, trazer risco operacional para as farmácias. A necessidade de fazer um pedido extra ou precisar organizar a farmácia quando o turno já está intenso consegue piorar uma situação que já estava ruim.')
    st.markdown('Além disso, trabalhar diariamente em um ritmo acelerado e intenso pode trazer certo desgaste físico e/ou emocional para os auxiliares de farmácia, abrindo margem para atestados e faltas, o que prejudica um plantão que já seria difícil.')
    
    st.header('Fechamento')
    st.markdown('Os resultados apresentados reforçam a importância da análise como suporte à tomada de decisão. A manutenção de indicadores estruturados e acompanhamento periódico permitirá identificar variações relevantes, sustentar melhorias nos processos e acompanhar de perto mudanças que afetem não apenas o cenário farmacêutico, mas também de enfermagem e cuidados com o paciente.')
    st.markdown('Esse estudo permitiu compreender de forma objetiva o comportamento da demanda e da eficiência operacional ao longo do período analisado e abre portas para o entendimento de tendências e preocupações na farmácia.')
    st.markdown('Recomenda-se a continuidade do monitoramento dos indicadores apresentados, garantindo acompanhamento preventivo de possíveis riscos operacionais.')

    st.markdown('Análise elaborada por <br>**Vinícius Oliveira** <br>Auxiliar de Farmácia - UTI 8º <br>Fevereiro/2026', unsafe_allow_html=True)

