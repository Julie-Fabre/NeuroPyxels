# -*- coding: utf-8 -*-
"""
2018-07-20
@author: Maxime Beau, Neural Computations Lab, University College London
"""
import os
import os.path as op

from psutil import disk_partitions; opj=op.join
from pathlib import Path

import pickle as pkl
from tqdm.auto import tqdm

import numpy as np
from math import floor, log10

import matplotlib
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoLocator
from cmcrameri import cm as cmcr
cmcr=cmcr.__dict__
from IPython.core.display import HTML,display

# Make matplotlib saved figures text text editable
mpl.rcParams["svg.fonttype"] = 'none'
mpl.rcParams['pdf.fonttype'] = 42 
mpl.rcParams['ps.fonttype'] = 42

# use Arial, damn it
if 'Arial' in [f.name for f in matplotlib.font_manager.fontManager.ttflist]:
    matplotlib.rcParams['font.family'] = 'Arial'
else:
    print("Oh no! Arial isn't on your system. We strongly recommend that you install Arial for your aesthetic sanity.")

from npyx.utils import phyColorsDic, npa, zscore, isnumeric, assert_iterable, save_np_array, pprint_dic, docstring_decorator
from npyx.stats import fractile_normal, fractile_poisson

from npyx.inout import read_metadata, extract_rawChunk, assert_chan_in_dataset, chan_map, predefined_chanmap
from npyx.gl import get_units
from npyx.merger import assert_multi, get_ds_ids
from npyx.spk_wvf import get_depthSort_peakChans, wvf, wvf_dsmatch, get_peak_chan, templates
from npyx.spk_t import trn, train_quality
from npyx.corr import acg, ccg, gen_sfc, get_cm, scaled_acg, acg_3D, convert_acg_log
from npyx.behav import align_times, get_processed_ifr, get_processed_popsync

#%% plotting utilities ##############################################################################################

default_mplp_params = dict(
            # title default parameters
            title_w='regular',
            title_s=22,

            # axes labels default parameters
            axlab_w='regular',
            axlab_s=22,

            # tick labels default parameters
            ticklab_w='regular',
            ticklab_s=22,
            ticks_direction='out',

            # ticks default parameters
            xtickrot=0,
            ytickrot=0,
            xtickha='center',
            xtickva='top',
            ytickha='right',
            ytickva='center',

            # spines and layout default parameters
            lw=1,
            hide_top_right=True,
            hide_axis=False,
            tight_layout=False,

            # legend default parameters
            show_legend=False,
            hide_legend=False,
            legend_loc=(1,1),

            # figure saving default parameters
            saveFig=False,
            saveDir = "~/Downloads",
            figname="figure",
            _format="pdf",

            # colorbar default parameters
            colorbar=False,
            cbar_w=0.03,
            cbar_h=0.4,
            clabel=None,
            clabel_w='regular',
            clabel_s=22,
            cticks_s=22,

            # horizontal and vertical lines default parameters
            hlines = None, # provide any iterable of values to plot horizontal lines along the y axis
            vlines = None, # provide any iterable of values to plot vertical lines along the x axis
            lines_kwargs = {'lw':1.5, 'ls':'--', 'color':'k', 'zorder':-1000}, # add any other matplotlib.lines.Line2D arguments
)

@docstring_decorator(pprint_dic(default_mplp_params))
def mplp(fig=None, ax=None, figsize=None, axsize=None,
         xlim=None, ylim=None, xlabel=None, ylabel=None,
         xticks=None, yticks=None, xtickslabels=None, ytickslabels=None,
         reset_xticks=None, reset_yticks=None,
         xtickrot=None, ytickrot=None,
         xtickha=None, xtickva=None, ytickha=None, ytickva=None,
         axlab_w=None, axlab_s=None,
         ticklab_w=None, ticklab_s=None, ticks_direction=None,
         title=None, title_w=None, title_s=None,
         lw=None, hide_top_right=None, hide_axis=None,
         tight_layout=None, hspace=None, wspace=None,
         show_legend=None, hide_legend=None, legend_loc=None,
         saveFig=None, saveDir = None, figname=None, _format="pdf",
         colorbar=None, vmin=None, vmax=None, cmap=None, cticks=None, ctickslabels=None, clim=None,
         cbar_w=None, cbar_h=None, clabel=None, clabel_w=None, clabel_s=None, cticks_s=None,
         hlines = None, vlines = None, lines_kwargs = None,
         prettify=True):
    """
    make plots pretty
    matplotlib plotter

    Awesome utility to format matplotlib plots.
    Simply add mplp() at the end of any plotting script, feeding it with your fav parameters!

    IMPORTANT If you set prettify = False, it will only reset the parameters that you provide actively, and leave the rest as is.

    In a breeze,
        - change the weight/size/alignment/rotation of the axis labels, ticks labels, title
        - edit the x, y and colorbar axis ticks and ticks labels
        - hide the splines (edges of your figure)
        - hide all the axis, label etc in one go with hide_axis
        - save figures in any format
        - add or remove a legend
        - add a custom colorbar
        - apply tight_layout to fit your subplots properly (in a way which prevents saved plots from being clipped)

    How it works: it will grab the currently active figure and axis (plt.gcf() and plt.gca()).
    Alternatively, you can pass a matplotlib figure and specific axes as arguments.

    Default Arguments:
        {0}
    """

    global default_mplp_params

    if fig is None:
        if ax is None:
            fig = plt.gcf()
        else:
            fig = ax.get_figure()
    if ax is None: ax=plt.gca()

    # if prettify is set to True (default),
    # mplp() will change the plot parameters in the background,
    # even if not actively passed
    if prettify:

        # limits default parameters
        if xlim is None: xlim = ax.get_xlim()
        if ylim is None: ylim = ax.get_ylim()

        # title default parameters
        if title is None: title = ax.get_title()
        if title_w is None: title_w = default_mplp_params['title_w']
        if title_s is None: title_s = default_mplp_params['title_s']

        # axes labels default parameters
        if ylabel is None: ylabel = ax.get_ylabel()
        if xlabel is None: xlabel = ax.get_xlabel()
        if axlab_w is None: axlab_w = default_mplp_params['axlab_w']
        if axlab_s is None: axlab_s = default_mplp_params['axlab_s']

        # tick labels default parameters
        if ticklab_w is None: ticklab_w = default_mplp_params['ticklab_w']
        if ticklab_s is None: ticklab_s = default_mplp_params['ticklab_s']
        if ticks_direction is None: ticks_direction = default_mplp_params['ticks_direction']

        # ticks default parameters
        if xtickrot is None: xtickrot = default_mplp_params['xtickrot']
        if ytickrot is None: ytickrot = default_mplp_params['ytickrot']
        if xtickha is None: xtickha = default_mplp_params['xtickha']
        if xtickva is None: xtickva = default_mplp_params['xtickva']
        if ytickha is None: ytickha = default_mplp_params['ytickha']
        if ytickva is None: ytickva = default_mplp_params['ytickva']

        # spines and layout default parameters
        if lw is None: lw = default_mplp_params['lw']
        if hide_top_right is None: hide_top_right = default_mplp_params['hide_top_right']
        if hide_axis is None: hide_axis = default_mplp_params['hide_axis']
        if tight_layout is None: tight_layout = default_mplp_params['tight_layout']

        # legend default parameters
        if show_legend is None: show_legend = default_mplp_params['show_legend']
        if hide_legend is None: hide_legend = default_mplp_params['hide_legend']
        if legend_loc is None: legend_loc = default_mplp_params['legend_loc']

        # figure saving default parameters
        if saveFig is None: saveFig = default_mplp_params['saveFig']
        if saveDir is None: saveDir = default_mplp_params['saveDir']
        if figname is None: figname = default_mplp_params['figname']
        if _format is None: _format = default_mplp_params['_format']

        # colorbar default parameters
        if colorbar is None: colorbar = default_mplp_params['colorbar']
        if cbar_w is None: cbar_w = default_mplp_params['cbar_w']
        if cbar_h is None: cbar_h = default_mplp_params['cbar_h']
        if clabel is None: clabel = default_mplp_params['clabel']
        if clabel_w is None: clabel_w = default_mplp_params['clabel_w']
        if clabel_s is None: clabel_s = default_mplp_params['clabel_s']
        if cticks_s is None: cticks_s = default_mplp_params['cticks_s']


    hfont = {'fontname':'Arial'}
    if figsize is not None:
        assert axsize is  None,\
            "You cannot set both the axes and figure size - the axes size is based on the figure size."
        fig.set_figwidth(figsize[0])
        fig.set_figheight(figsize[1])
    if axsize is not None:
        assert figsize is  None,\
            "You cannot set both the axes and figure size - the axes size is based on the figure size."
        set_ax_size(ax, *axsize)

    # Opportunity to easily hide everything
    if hide_axis is not None:
        if hide_axis:
            ax.axis('off')
        else: ax.axis('on')

    # Axis labels
    if ylabel is not None: ax.set_ylabel(ylabel, weight=axlab_w, size=axlab_s, **hfont)
    if xlabel is not None: ax.set_xlabel(xlabel, weight=axlab_w, size=axlab_s, **hfont)

    # Setup x/y limits BEFORE altering the ticks
    # since the limits will alter the ticks
    if xlim is not None: ax.set_xlim(xlim)
    if ylim is not None: ax.set_ylim(ylim)

    # Tick values
    if prettify and xticks is None:
        if reset_xticks:
            ax.xaxis.set_major_locator(AutoLocator())
        xticks = ax.get_xticks()
    if xticks is not None: ax.set_xticks(xticks)

    if prettify and yticks is None:
        if reset_yticks:
            ax.yaxis.set_major_locator(AutoLocator())
        yticks = ax.get_yticks()
    if yticks is not None: ax.set_yticks(yticks)

    # Tick labels
    fig.canvas.draw() # To force setting of ticklabels
    if xtickslabels is None and prettify:
        if any(ax.get_xticklabels()):
            if isnumeric(ax.get_xticklabels()[0].get_text()):
                xtickslabels, x_nflt = get_labels_from_ticks(xticks)
            else:
                xtickslabels = ax.get_xticklabels()
    if ytickslabels is None and prettify:
        if any(ax.get_yticklabels()):
            if isnumeric(ax.get_yticklabels()[0].get_text()):
                ytickslabels, y_nflt = get_labels_from_ticks(yticks)
            else:
                ytickslabels = ax.get_yticklabels()

    if xtickslabels is not None:
        if xticks is not None:
            assert len(xtickslabels)==len(xticks),\
                'WARNING you provided too many/few xtickslabels! Make sure that the default/provided xticks match them.'
        if xtickha is None: xtickha = ax.xaxis.get_ticklabels()[0].get_ha()
        if xtickva is None: xtickva = ax.xaxis.get_ticklabels()[0].get_va()
        ax.set_xticklabels(xtickslabels, fontsize=ticklab_s, fontweight=ticklab_w,
                            color=(0,0,0), **hfont, rotation=xtickrot, ha=xtickha, va=xtickva)
    if ytickslabels is not None:
        if yticks is not None:
            assert len(ytickslabels)==len(yticks),\
                'WARNING you provided too many/few ytickslabels! Make sure that the default/provided yticks match them.'
        if ytickha is None: ytickha = ax.yaxis.get_ticklabels()[0].get_ha()
        if ytickva is None: ytickva = ax.yaxis.get_ticklabels()[0].get_va()
        ax.set_yticklabels(ytickslabels, fontsize=ticklab_s, fontweight=ticklab_w,
                            color=(0,0,0), **hfont, rotation=ytickrot, ha=ytickha, va=ytickva)

    # Reset x/y limits a second time
    if xlim is not None: ax.set_xlim(xlim)
    if ylim is not None: ax.set_ylim(ylim)

    # Title
    if title is not None: ax.set_title(title, size=title_s, weight=title_w)

    # Ticks and spines aspect
    if prettify:
        ax.tick_params(axis='both', bottom=1, left=1, top=0, right=0, width=lw, length=4, direction=ticks_direction)
    elif lw is not None or ticks_direction is not None:
        ax.tick_params(axis='both', width=lw, direction=ticks_direction)

    if hide_top_right is not None:
        spine_keys = list(ax.spines.keys())
        hide_spine_keys = ['polar'] if 'polar' in spine_keys else ['top', 'right']
        lw_spine_keys = ['polar'] if 'polar' in spine_keys else ['left', 'bottom', 'top', 'right']
        if hide_top_right and 'top' in hide_spine_keys: [ax.spines[sp].set_visible(False) for sp in hide_spine_keys]
        else: [ax.spines[sp].set_visible(True) for sp in hide_spine_keys]
        for sp in lw_spine_keys:
            ax.spines[sp].set_lw(lw)

    # Optionally plot horizontal and vertical dashed lines
    if lines_kwargs is None: lines_kwargs = {}
    l_kwargs = default_mplp_params['lines_kwargs']
    l_kwargs.update(lines_kwargs) # prevalence of passed arguments

    if hlines is not None:
        assert hasattr(hlines, '__iter__'), 'hlines must be an iterable!'
        for hline in hlines:
            ax.axhline(y=hline, **l_kwargs)
    if vlines is not None:
        assert hasattr(vlines, '__iter__'), 'vlines must be an iterable!'
        for vline in vlines:
            ax.axvline(x=vline, **l_kwargs)

    # Aligning and spacing axes and labels
    if tight_layout: fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    if hspace is not None: fig.subplots_adjust(hspace=hspace)
    if wspace is not None: fig.subplots_adjust(wspace=wspace)
    if prettify:
        axis_to_align = [AX for AX in fig.axes if 'AxesSubplot' in AX.__repr__()]
        fig.align_ylabels(axis_to_align)
        fig.align_xlabels(axis_to_align)

    assert not (show_legend and hide_legend),\
        "You instructed to both show and hide the legend...?"
    if legend_loc is not None:
        assert len(legend_loc)==2 or len(legend_loc)==4,\
            "legend_loc must comply to the bbox_to_anchor format ( (x,y) or (x,y,width,height))."
    if show_legend: plt.legend(bbox_to_anchor=legend_loc, prop={'family':'Arial'})
    elif hide_legend: plt.legend([],[], frameon=False)

    if colorbar:
        assert vmin is not None and vmax is not None and cmap is not None,\
            "You must provide vmin, vmax and cmap to show a colorbar."
        fig = add_colorbar(fig, ax, None, vmin, vmax,
                 cbar_w, cbar_h, cticks, clabel, clabel_w, clabel_s, cticks_s, ctickslabels, cmap,
                 clim=clim) 

    if prettify:
        fig.patch.set_facecolor('white')
    if saveFig:
        if figname is None and title is not None:
            figname = title
        save_mpl_fig(fig, figname, saveDir, _format, dpi=500)

    return fig, ax

def save_mpl_fig(fig, figname, saveDir, _format, dpi=500):

    # Fix matplotlib resolution and make text editable
    dpi_orig = mpl.rcParams['figure.dpi']
    fonttype1 = mpl.rcParams['pdf.fonttype']
    fonttype2 = mpl.rcParams['ps.fonttype']

    mpl.rcParams['figure.dpi']=dpi
    mpl.rcParams['pdf.fonttype']=42
    mpl.rcParams['ps.fonttype']=42

    if saveDir is None: saveDir = '~/Downloads'
    saveDir=Path(saveDir).expanduser()
    if not saveDir.exists():
        assert saveDir.parent.exists(), f'WARNING can only create a path of a single directory level, {saveDir.parent} must exist already!'
        saveDir.mkdir()
    p=saveDir/f"{figname}.{_format}"
    fig.savefig(p, dpi=dpi, bbox_inches='tight')

    # restaure original parameters
    mpl.rcParams['figure.dpi']=dpi_orig
    mpl.rcParams['pdf.fonttype']=fonttype1
    mpl.rcParams['ps.fonttype']=fonttype2
    # platform=sys.platform
    # if platform=='linux':
    #     bashCommand = f'sudo chmod a+rwx {p}'
    #     process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    #     output, error = process.communicate()

def plot_scalebar(ax, xscalebar=None, yscalebar=None,
                  x_unit="ms", y_unit="\u03BCV",
                  scalepad=0.025, fontsize=14, lw=3,
                  loc='right',
                  offset_x = 0, offset_y = 0):
    
    """
    Add x and/or y scalebar at the bottom of a matplotlib axis.
    
    Arguments:
        - ax: matplotlib axis
        - xscalebar: float, length of x scalebar in units of x axis.
                        If None, no x scalebar is added.
        - yscalebar: float, length of y scalebar in units of y axis
                        If None, no y scalebar is added.
        - x_unit: str, unit of x axis
        - y_unit: str, unit of y axis
        - scalepad: float, padding between scalebar and axis,
                    in fraction of axis height (arbitrary, could have been width)
        - fontsize: float, fontsize of scalebar text
        - lw: float, linewidth of scalebar
        - loc: str, location of scalebar, either 'left' or 'right'
        - offset_x: float, additional offset of scalebar in x direction,
                    in fraction of axis width (+ or -)
        - offset_y: float, additional offset of scalebar in y direction,
                    in fraction of axis height (+ or -)
    """
    
    # process arguments
    assert xscalebar is not None or yscalebar is not None,\
        "WARNING you must provide either xscalebar or yscalebar. Don't you want to plot a scalebar?"
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    axw, axh = np.diff(xlim)[0], np.diff(ylim)[0]
    bbox = ax.get_window_extent().transformed(ax.get_figure().dpi_scale_trans.inverted())
    axw_inch, axh_inch = bbox.width, bbox.height

    vpad = scalepad*axh
    hpad = scalepad*axw * (axh_inch/axw_inch)

    offset_x = float(offset_x*axw)
    offset_y = float(offset_y*axh)
    assert loc in ['left', 'right']
    if loc == 'right':
        offset_x = offset_x-0.1
    else:
        offset_x = offset_x+0.1
    offset_y = offset_y + 0.1

    # x scalebar
    if xscalebar is not None:
        xscale_y = [ylim[0], ylim[0]]
        if yscalebar is None:
            text_pos_sign = 1
            xscale_va = "bottom"
        else:
            text_pos_sign = -1
            xscale_va = "top"
        if loc == 'right':
            xscale_x = [xlim[1]-xscalebar, xlim[1]]
        else:
            xscale_x = [xlim[0], xlim[0]+xscalebar]

        # optional offset
        xscale_x = [x+offset_x for x in xscale_x]
        xscale_y = [y+offset_y for y in xscale_y]

        # plot xscalebar
        ax.plot(xscale_x, xscale_y, c='k', lw=lw)

        # plot xscalebar text
        ax.text(xscale_x[0]+np.diff(xscale_x)/2,
                xscale_y[0]+vpad*text_pos_sign,
                f"{xscalebar}{x_unit}",
                ha="center", va=xscale_va, fontsize=fontsize)

    # y scalebar
    if yscalebar is not None:
        yscale_y = [ylim[0], ylim[0]+yscalebar]
        if xscalebar is None:
            if loc == 'right':
                text_pos_sign = -1
                yscale_ha = "right"
            else:
                text_pos_sign = 1
                yscale_ha = "left"
        else:
            if loc == 'right':
                text_pos_sign = 1
                yscale_ha = "left"
            else:
                text_pos_sign = -1
                yscale_ha = "right"
        if loc == 'right':
            yscale_x = [xlim[1], xlim[1]]
        else:
            yscale_x = [xlim[0], xlim[0]]

        # optional offset
        yscale_x = [x+offset_x for x in yscale_x]
        yscale_y = [y+offset_y for y in yscale_y]

        # plot yscalebar
        ax.plot(yscale_x, yscale_y, c='k', lw=lw)
        # plot yscalebar text
        ax.text(yscale_x[0]+hpad*text_pos_sign, yscale_y[0]+np.diff(yscale_y)/2,
                f"{yscalebar}{y_unit}",
                ha=yscale_ha, va="center", fontsize=fontsize)
    

def mplshow(fig):

    # create a dummy figure and use its
    # manager to display "fig"

    dummy = plt.figure()
    new_manager = dummy.canvas.manager
    new_manager.canvas.figure = fig
    fig.set_canvas(new_manager.canvas)

def bkshow(bkfig, title=None, save=0, savePath='~/Downloads'):
    import bokeh as bk

    if title is None: title=bkfig.__repr__()
    if save:bk.plotting.output_file(f'{title}.html')
    bk.plotting.show(bkfig)

def hvshow(hvobject, backend='matplotlib', return_mpl=False):
    '''
    Holoview utility which
    - for dynamic display, interaction and data exploration:
        in browser, pops up a holoview object as a bokeh figure
    - for static instanciation, refinement and data exploitation:
        in matplotlib current backend, pops up a holoview object as a matplotlib figure
        and eventually returns it for further tweaking.
    Arguments:
        - hvobject: a Holoviews object e.g. Element, Overlay or Layout.
        - backend: 'bokeh' or 'matplotlib', which backend to use to show figure
        - return_mpl: bool, returns a matplotlib figure

    '''
    import holoviews as hv

    assert backend in ['bokeh', 'matplotlib']
    if backend=='matplotlib' or return_mpl:
        mplfig=hv.render(hvobject, backend='matplotlib')
    if backend=='bokeh': bkshow(hv.render(hvobject, backend='bokeh'))
    elif backend=='matplotlib': mplshow(mplfig)
    if return_mpl: return mplfig


def mpl_pickledump(fig, figname, path):
    path=Path(path)
    assert path.exists(), 'WARNING provided target path does not exist!'
    figname+='.pkl'
    pkl.dump(fig, open(path/figname,'wb'))

def mpl_pickleload(fig_path):
    fig_path=Path(fig_path)
    assert fig_path.exists(), 'WARNING provided figure file path does not exist!'
    assert str(fig_path)[-4:]=='.pkl', 'WARNING provided figure file path does not end with .pkl!'
    return pkl.load(  open(fig_path,  'rb')  )

def mpl_axi_axpos(nrows, ncols, i):
    '''Converts matplotlib subplot index (as in 232 = 2x3 grid, 2nd subplot)
       into (row,col) axes grid location (in this example 0,1)'''
    ax_ids=np.arange(nrows*ncols).reshape((nrows,ncols))+1
    pos=np.argwhere(ax_ids==i)[0]
    assert any(pos), f'WARNING index {i} is too big given {nrows} rows and {ncols} columns!'
    return pos

#### Plot ticks and colors utilities ####

def myround(x, base=5):
    return base * np.round(x/base)

def myceil(x, base=5):
    return base * np.ceil(x/base)

def myfloor(x, base=5):
    return base * np.floor(x/base)

def ceil_power10(x):
    return 10**np.ceil(np.log10(x))

def n_decimals(x):
    return len(str(x).split('.')[1])

def get_bestticks(start, end, step=None, light=False):
    """
    Returns the best ticks for a given array of values (i.e. an sparser array of equally spaced values).
    If the array if np.arange(10), the returned array will be np.arange(0,10,1).
    If np.arange(50), the returned array will be np.arange(0,50,5). And so on.
    """
    span = end - start
    if step is None:
        upper10=ceil_power10(span)
        if span<=upper10/5:
            step=upper10*0.01
        elif span<=upper10/2:
            step=upper10*0.05
        else:
            step=upper10*0.1
    if light: step=2*step
    assert step<span, f'Step {step} is too large for array span {span}!'
    ticks=np.arange(myceil(start,step),myfloor(end,step)+step,step)
    ticks=np.round(ticks, n_decimals(step))
    if step==int(step):ticks=ticks.astype(np.int64)

    return ticks

def get_bestticks_from_array(arr, step=None, light=False):
    """
    Returns the best ticks for a given array of values (i.e. an sparser array of equally spaced values).
    If the array if np.arange(10), the returned array will be np.arange(0,10,1).
    If np.arange(50), the returned array will be np.arange(0,50,5). And so on.
    """
    arr = np.array(arr)
    start, end = 0, len(arr)-1
    ticks_i = get_bestticks(start, end, step, light)
    ticks = arr[ticks_i]

    return ticks

def get_labels_from_ticks(ticks):
    ticks=npa(ticks)
    nflt=0
    for t in ticks:
        t=round(t,4)
        for roundi in range(4):
            if t == round(t, roundi):
                if nflt<(roundi):nflt=roundi
                break
    ticks_labels=ticks.astype(np.int64) if nflt==0 else np.round(ticks.astype(float), nflt)
    jump_n=1 if nflt==0 else 2
    ticks_labels=[str(l)+'0'*(nflt+jump_n-len(str(l).replace('-',''))) for l in ticks_labels]
    return ticks_labels, nflt

def sci_notation(num, decimal_digits=1, precision=None, exponent=None):
    """
    Returns a string representation of the scientific
    notation of the given number formatted for use with
    LaTeX or Mathtext, with specified number of significant
    decimal digits and precision (number of decimal digits
    to show). The exponent to be used can also be specified
    explicitly.
    """
    if exponent is None:
        exponent = int(floor(log10(abs(num))))
    coeff = round(num / float(10**exponent), decimal_digits)
    if precision is None:
        precision = decimal_digits

    return r"${0:.{2}f}\cdot10^{{{1:d}}}$".format(coeff, exponent, precision)

def get_all_mpl_colors():
    mpl_colors=get_mpl_css_colors(sort=True, aslist=False)
    mpl_colors={**mpl_colors,**matplotlib.colors.BASE_COLORS}
    mpl_colors={**mpl_colors,**matplotlib.colors.TABLEAU_COLORS}
    return mpl_colors

def get_mpl_css_colors(sort=True, aslist=False):
    colors=matplotlib.colors.CSS4_COLORS
    if sort:
        by_hsv = sorted((tuple(mpl.colors.rgb_to_hsv(mpl.colors.to_rgb(color))),
                         name)
                        for name, color in colors.items())
        colors={name:colors[name] for hsv, name in by_hsv}
    if aslist: colors=list(colors.values())
    return colors

def mpl_hex(color):
    'converts a matplotlib string name to its hex representation.'
    mpl_colors=get_all_mpl_colors()
    message='color should be a litteral string recognized by matplotlib.'
    assert isinstance(color, str), message
    basecolors={'b': 'blue', 'g': 'green', 'r': 'red', 'c': 'cyan', 'm': 'magenta', 'y': 'yellow', 'k': 'black', 'w': 'white'}
    if color in basecolors.keys(): color=basecolors[color]
    assert color in mpl_colors.keys(), message
    return mpl_colors[color]

def hex_rgb(color):
    'converts a hex color to its rgb representation.'
    message='color must be a hex string starting with #.'
    assert color[0]=='#', message
    return tuple(int(color[1:][i:i+2], 16)/255 for i in (0, 2, 4))

def to_rgb(color):
    'converts a matplotlib string name or hex string to its rgb representation.'
    message='color must either be a litteral matplotlib string name or a hex string starting with #.'
    assert isinstance(color, str), message
    mpl_colors=get_all_mpl_colors()
    if color in mpl_colors.keys(): color=mpl_hex(color)
    assert color[0]=='#', message
    return hex_rgb(color)

def to_hsv(color):
    if isinstance(color,str):
        color=to_rgb(color)
    return mpl.colors.rgb_to_hsv(color)

def to_hex(color):
    'rgb or matplotlib litteral representation to hex representation'
    if isinstance(color,str):
        return mpl_hex(color)
    return rgb_hex(color)

def rgb_hex(color):
    '''converts a (r,g,b) color (either 0-1 or 0-255) to its hex representation.
    for ambiguous pure combinations of 0s and 1s e,g, (0,0,1), (1/1/1) is assumed.'''
    message='color must be an iterable of length 3.'
    assert assert_iterable(color), message
    assert len(color)==3, message
    if all([(c<=1)&(c>=0) for c in color]): color=[int(round(c*255)) for c in color] # in case provided rgb is 0-1
    color=tuple(color)
    return '#%02x%02x%02x' % color

def html_palette(colors, maxwidth=20, as_str=False, show=True):
    'colors must be a list of (r,g,b) values ([0-255 or 0-1]) or hex strings.'
    s=55
    n=min(len(colors),maxwidth)
    col_rows=[colors[i*maxwidth:i*maxwidth+maxwidth] for i in range(len(colors)//maxwidth+1)]
    col_rows=[c for c in col_rows if any(c)]
    h=len(col_rows)
    palette = f'<svg  width="{n * s}" height="{s * h}">'
    for r,colors in enumerate(col_rows):
        for i, c in enumerate(colors):
            if not isinstance(c,str):c=rgb_hex(c)
            palette += (
                f'<rect x="{i * s}" y="{r*s}" width="{s}" height="{s}" style="fill:{c};'
                f'stroke-width:2;stroke:rgb(255,255,255)"/>'
            )
    palette += '</svg>'
    if not as_str: palette = HTML(palette)
    if show and not as_str: display(palette)
    return palette

def get_cmap(cmap_str):
    if cmap_str in list(cmcr.keys()):
        return cmcr[cmap_str]
    else:
        return mpl.cm.get_cmap(cmap_str)

def get_bounded_cmap(cmap_str, vmin, center, vmax, colorseq='linear'):
    assert vmin<=center<=vmax, 'WARNING vmin >center or center>vmax!!'
    cmap = get_cmap(cmap_str)

    vrange = max(vmax - center, center - vmin)
    if vrange==0: vrange=1
    if colorseq=='linear':
        vrange=[-vrange,vrange]
        cmin, cmax = (vmin-vrange[0])/(vrange[1]-vrange[0]), (vmax-vrange[0])/(vrange[1]-vrange[0])
        colors_reindex = np.linspace(cmin, cmax, 256)
    elif colorseq=='nonlinear':
        topratio=(vmax - center)/vrange
        bottomratio=abs(vmin - center)/vrange
        colors_reindex=np.append(np.linspace(0, 0.5, int(256*bottomratio/2)),np.linspace(0.5, 1, int(256*topratio/2)))
    cmap = mpl.colors.ListedColormap(cmap(colors_reindex))

    return cmap

def get_ncolors_cmap(n, cmap_str="tab10", plot=False):
    '''Returns homogeneously distributed n colors from specified colormap.
    Arguments:
        - cmap_str: str, matplotlib or crameri colormap
        - n_ int, n colors
        - plot: bool, whether to display colormap in HTML (works in jupyter notebooks)
    Returns:
        - colors: list of n colors homogeneously tiling cmap_str
    '''
    assert n==int(n)
    n=int(n)
    cmap = get_cmap(cmap_str)
    ids=np.linspace(0,1,n)
    colors = cmap(ids)[:,:-1].tolist() # get rid of alpha
    if plot:
        html_palette(colors, 20, 0, 1)
    return colors

def get_color_families(ncolors, nfamilies, cmapstr=None, gap_between_families=4):
    '''
    Return nfamilies of ncolors colors which are perceptually closer within than between families.

    Within each family, the colors are neighbours on a perceptually sequential colormap.

    Between each family, stand gap_between_families colors.
    Increase this value to make colors within families more similar and colors between families more distinct.

    If you decide to provide a cmap, it NEEDS to be perceptually sequential,
    as this function assumes that colors with close ranks are perceptually close.
    If no cmap is provided, the matplotlib literal colors sorted by HSV are used by default.

    '''
    if cmapstr is None:
        colors_all=get_mpl_css_colors(sort=True, aslist=True)[15:-10]
        colors=npa(colors_all)[np.linspace(0,len(colors_all)-1,(ncolors+gap_between_families)*nfamilies).astype(np.int64)].tolist()
    else:
        colors=get_ncolors_cmap((ncolors+gap_between_families//2)*nfamilies, cmapstr, plot=False)
    highsat_colors=[c for c in colors if to_hsv(c)[1]>0.4]
    seed_ids=np.linspace(0, len(highsat_colors)-ncolors, nfamilies).astype(np.int64)

    color_families=[[highsat_colors[si+i] for i in range(ncolors)] for si in seed_ids]

    return color_families

def format_colors(colors):
    '''
    Turns single color or iterable of colors into an iterable of colors.
    '''
    # If string: single letter or hex, can simply use flatten
    if type(npa([colors]).flatten()[0]) in [str, np.str_]:
        colors=npa([colors]).flatten()
    # if list of tuples, cannot flatten them!
    else:
        if type(colors[0]) in [float, np.float16, np.float32, np.float64]:
            colors=npa([colors,])
        else:
            colors=npa(colors)
    return colors

def set_ax_size(ax,w,h):
    """ w, h: width, height in inches """
    if not ax: ax=plt.gca()
    l = ax.figure.subplotpars.left
    r = ax.figure.subplotpars.right
    t = ax.figure.subplotpars.top
    b = ax.figure.subplotpars.bottom
    figw = float(w)/(r-l)
    figh = float(h)/(t-b)
    ax.figure.set_size_inches(figw, figh)

#%% Exploratory plots

def hist_MB(arr, a=None, b=None, s=None,
            title='', xlabel='', ylabel='', legend_label=None,
            ax=None, color=None, alpha=1, figsize=None, xlim=None,
            saveFig=False, saveDir='', _format='pdf', prettify=True,
            style='bar', density=False, **mplp_kwargs):
    """
    Plot histogram of array arr.
    Arguments:
        - arr: array, data to plot
        - a: float, lower bound of histogram
        - b: float, upper bound of histogram
        - s: float, bin size
        - title: str, title of plot
        - xlabel: str, label of x axis
        - ylabel: str, label of y axis
        - ax: matplotlib axis, axis to plot on (new figure is created if none is provided)
        - color: str, color of bars
        - alpha: float, opacity of bars
        - figsize: tuple, size of figure
        - xlim: tuple, limits of x axis
        - saveFig: bool, whether to save figure or not
        - saveDir: str, directory to save figure to
        - _format: str, format to save figure to
        - prettify: bool, whether to apply mplp() prettification or not
        - **mplp_kwargs: any additional formatting parameters, passed to mplp()
    """
    assert style in ['bar', 'step'], 'style must be either bar or step!'
    if a is None: a=np.min(arr)
    if b is None: b=np.max(arr)
    if s is None: s=(b-a)/100
    hist=np.histogram(arr, bins=np.arange(a,b+s,s), density=density)
    y=hist[0]
    x=hist[1][:-1] + np.diff(hist[1][:2])/2
    if ax is None:
        (fig, ax) = plt.subplots()
    else:
        fig, ax = ax.get_figure(), ax
    if style == 'bar':
        ax.bar(x=x, height=y, width=s, color=color, edgecolor='k', alpha=alpha, label=legend_label)
    elif style == 'step':
        x_step = np.concatenate((x[0:1]-s, x, [x[-1]+s]))
        y_step = np.concatenate(([0], y, [0]))
        ax.step(x_step, y_step, where='mid', color=color)
        ax.fill_between(x_step, y_step*0, y_step, step='mid', color=color, alpha=alpha, label=legend_label)
        ax.set_ylim(bottom=0)
    ax.set_title(title)
    ax.set_xlabel(xlabel) if len(xlabel)>0 else ax.set_xlabel(f'Binsize:{s:.2f}')
    ax.set_ylabel(ylabel) if len(ylabel)>0 else ax.set_ylabel({False:'Counts', True:'Density'}[density])

    if xlim is None: xlim = [a,b]
    show_legend = True if legend_label else None
    fig, ax = mplp(fig, ax, xlim=xlim, figsize=figsize,
                  prettify=prettify, show_legend=show_legend,
                  **mplp_kwargs)

    if saveFig: save_mpl_fig(fig, title, saveDir, _format)
      
    return fig

def paired_plot(df, cats, ylabel=None, xlabel=None, color="grey",
               dodge=True, dodge_range=0.1,
               figsize=(3,5), prettify=True, **mplp_kwargs):
    """
    Plot scatter plot of each column of dataframe df against the first column,
    in a paired-plot fashion (rows are linked by a line).
    Arguments:
        - df: pandas dataframe
        - cats: list of str, columns of dataframe df
        - ylabel: str, label of y axis
        - xlabel: str, label of x axis
        - color: str, color of points
        - dodge: bool, whether to randomly offset points so that they do not overlap
        - dodge_range: float, range of random offset
        - figsize: (x,y) tuple, size of figure in inches
        - prettify: bool, whether to apply mplp() prettification or not
        - **mplp_kwargs: any additional formatting parameters, passed to mplp()
    """

    plt.figure()

    x0=df[cats[0]]*0
    l=len(x0)

    lines_x = np.zeros((len(cats), l))
    lines = np.zeros((len(cats), l))
    for i, cat in enumerate(cats):
        x = x0+i
        if dodge: x += np.random.uniform(-dodge_range, dodge_range, l)
        y = df[cat]
        assert len(y) == l
        plt.scatter(x, y, color=color, edgecolor='k')

        lines_x[i,:]=x
        lines[i,:]=y

    plt.plot(lines_x, lines, color=color, alpha=0.5, zorder=-1)

    mplp(figsize=figsize, ylabel=ylabel, xlabel=xlabel,
         xlim=[-0.5, i+0.5], xticks=np.arange(i+1), xtickslabels=cats,
         prettify=prettify, **mplp_kwargs)


#%% Stats plots ##############################################################################################

def plot_pval_borders(Y, p, dist='poisson', Y_pred=None, gauss_baseline_fract=1, x=None, ax=None, color=None,
                      ylabel=None, xlabel=None, title=None, prettify=True, **mplp_kwargs):
    '''
    Function to plot array X and the upper and lower borders for a given p value.
    Arguments:
        - Y: np array
        - p:float, p value to plot threshold [0-1]
        - dist: whether to assume Poisson or Normal distribution
        - Y_pred: np array or same size as Y, predictor for distribution (If none is provided, the mean of X is used)
        - gauss_baseline_fract: float, fraction of data to use as baseline for normal distribution
        - x: np array, x axis values
        - ax: matplotlib axis, axis to plot on (new figure is created if none is provided)
        - color: str, color of bars
        - ylabel: str, label of y axis
        - xlabel: str, label of x axis
        - title: str, title of plot
        - prettify: bool, whether to apply mplp() prettification or not
        - **mplp_kwargs: any additional formatting parameters, passed to mplp()
    '''
    Y=npa(Y)
    assert 0<p<1
    assert dist in ['poisson', 'normal']
    if ax is None: fig, ax = plt.subplots()
    else: fig=ax.get_figure()

    if dist=='poisson':
        assert (Y_pred is not None) and (len(Y_pred)==len(Y)), 'When plotting Poisson distribution, you need to provide a predictor with the same shape as X!'
        fp1=[fractile_poisson(p/2, l=c) for c in Y_pred]
        fp2=[fractile_poisson(1-p/2, l=c) for c in Y_pred]
    elif dist=='normal':
        Y_baseline=np.append(Y[:int(len(Y)*gauss_baseline_fract/2)],Y[int(len(Y)*(1-gauss_baseline_fract/2)):])
        Y_pred=np.ones(Y.shape[0])*np.mean(Y_baseline)
        fp1=np.ones(Y.shape[0])*fractile_normal(p=p/2, m=np.mean(Y_baseline), s=np.std(Y_baseline))
        fp2=np.ones(Y.shape[0])*fractile_normal(p=1-p/2, m=np.mean(Y_baseline), s=np.std(Y_baseline))

    if x is None: x=np.arange(len(Y))
    ax.plot(x,Y, c=color)
    ax.plot(x,Y_pred, c='k', ls='--', label='predictor')
    ax.plot(x,fp1, c='r', ls='--', label='pval:{}'.format(p))
    ax.plot(x,fp2, c='r', ls='--')
    ax.legend(fontsize=14)

    fig, ax = mplp(fig, ax, ylabel=ylabel, xlabel=xlabel,
                   title=title, prettify=prettify, **mplp_kwargs)

    return fig

def plot_fp_fn_rates(train, period_s, amplitudes, good_spikes_m,
                     fp=None, fn=None, fp_t=None, fn_t=None, fp_threshold=0.05, fn_threshold=0.05,
                     good_fp_periods=None, good_fn_periods=None, title=None, axis=None,
                     downsample=0.1):
    """
    - train: seconds
    - downsample: [0-1] value, if not None fraction of amplitudes to plot
    """
    if fp is not None and fn is not None:
        fp_ok, fn_ok = len(fp)>0, len(fn)>0
    else:
        fp_ok, fn_ok = False, False
    n_rows=1+int(fp_ok)+int(fn_ok)
    if axis is None:
        fig, axs = plt.subplots(n_rows, 1, figsize=(8, n_rows*3), sharex=True)
    else:
        axs = axis
    if n_rows==1: axs=[axs]
    x1,x2 = train[0], train[-1]
    axi=0
    if axis is not None:
        pass
    else:
        if fp_ok:
            axs[axi].scatter(fp_t, fp, color='firebrick')
            axs[axi].plot([x1,x2], [fp_threshold,fp_threshold], c='r', alpha=0.5)
            axs[axi].set_ylabel("FP rate")
            axi+=1
        if fn_ok:
            axs[axi].scatter(fn_t, fn, color='teal')
            axs[axi].plot([x1,x2], [fn_threshold,fn_threshold], c='r', alpha=0.5)
            axs[axi].plot(ls="--")
            axs[axi].set_ylabel("FN rate")
            axi+=1
    if downsample is not None:
        sample = np.random.choice(len(amplitudes), int(len(amplitudes)*downsample), replace=False)
        train = train[sample]
        amplitudes = amplitudes[sample]
        good_spikes_m = good_spikes_m[sample]
            
    axs[axi].scatter((train)[good_spikes_m], amplitudes[good_spikes_m], color='green', alpha=0.5, s=10)
    axs[axi].scatter((train)[~good_spikes_m], amplitudes[~good_spikes_m], color='k', alpha=0.5, s=10)
    min_amp=np.min(amplitudes)
    axs[axi].plot([x1,x2], [min_amp,min_amp], color='grey', lw=0.5, zorder=-1)
    if good_fp_periods is not None:
        for per in good_fp_periods:
            axs[axi].plot(per, [5,5], color='firebrick', lw=3)
    if good_fn_periods is not None:
        for per in good_fn_periods:
            axs[axi].plot(per, [0,0], color='teal', lw=3)
    axs[axi].set_xlabel("Time (s)")
    axs[axi].set_ylabel("Amplitudes (a.u.)")
    axs[axi].set_xlim(period_s)
    
    if title is not None:
        fig.suptitle(title)
    if axis is None:
        return fig
    else:
        return axs

#%% Waveforms or raw data ##############################################################################################

def plot_wvf(dp, u=None, Nchannels=12, chStart=None, n_waveforms=300, t_waveforms=2.8,
             periods='all', spike_ids=None, wvf_batch_size=10, ignore_nwvf=True, again=False,
             whiten=False, med_sub=False, hpfilt=False, hpfiltf=300, nRangeWhiten=None, nRangeMedSub=None,
             title = None, plot_std=True, plot_mean=True, plot_templates=False, color='dodgerblue',
             labels=False, show_channels=True, scalebar_w=5, ticks_lw=1, sample_lines=0, ylim=[0,0],
             saveDir='~/Downloads', saveFig=False, saveData=False, _format='pdf',
             ignore_ks_chanfilt = True,
             ax_edge_um_x=22, ax_edge_um_y=18, margin=0.12, figw_inch=6, figh_inch=None,
             as_heatmap=False, use_dsmatch=False, verbose=False):
    '''
    To plot main channel alone: use Nchannels=1, chStart=None
    Arguments:
        - dp: string, datapath to kilosort directory
        - u: int, unit index
        - Nchannels: int, number of channels where waveform is plotted
        - chStart: int, channel from which to plot consecutive Nchannels | Default None, will then center on the peak channel.
        - n_waveforms: int, number of randomly sampled waveforms from which the mean and std are computed
        - t_waveforms: float, time span of the waveform samples around spike onset, in ms

        - periods: 'all' or list of (start, end) tuples, time periods in SECONDS to extract waveforms from
        - spike_ids: array, ids of spikes to use for plotting (rank across all spikes in the recording, across all units).
                     If None, falls back to other means of selection.
        - wvf_batch_size: int, number of waveforms to load at once. If None, loads all waveforms at once.
        - ignore_nwvf: boolean, whether to ignore n_waveforms and load all spikes in the specified periods/with the specified ids.
        - again: boolean, whether to reload waveforms from disk
        - whiten: boolean, whether to whiten waveforms
        - med_sub: boolean, whether to median-subtract waveforms
        - hpfilt: boolean, whether to high-pass filter waveforms
        - hpfiltf: float, high-pass filter frequency
        - nRangeWhiten: (min, max) tuple, range of channels to use for whitening
        - nRangeMedSub: (min, max) tuple, range of channels to use for median subtraction

        - title: string, plot title
        - plot_std: boolean, whether or not to plot the underlying standard deviation area | default True
        - plot_mean: boolean, whether or not to plot the mean waveform | default True
        - plot_templates: boolean, whether or not to plot the waveform template | default True
        - color: (r,g,b) tuple, hex or matplotlib litteral string, color of the mean waveform | default black
        - labels: boolean, whether to plot or not the axis, axis labels, title...
                  If False, only waveforms are plotted along with a scale bar. | Default False
        - show_channels: boolean, whether to show channel numbers | Default True
        - scalebar_w: float, width of scale bar in ms | Default 5
        - ticks_lw: float, width of ticks | Default 1
        - sample_lines: 'all' or int, whether to plot all or sample_lines individual samples in the background. Set to 0 to plot nothing.
        - ylim: upper limit of plots, in uV
        
        - saveDir  | default False
        - saveFig: boolean, save figure source data to saveDir | default Downloads
        - saveData: boolean, save waveforms source data to saveDir | default Downloads
        - _format: string, figure saving format (any format accepted by matplotlib savefig). | Default: pdf
        - ignore_ks_chanfilt: bool, whether to ignore kilosort channel filtering (some are jumped if low activity)

        - ax_edge_um_x: float, width of subplot (electrode site) in micrometers, relatively to the electrode channel map | Default 20
        - ax_edge_um_y: float, height of subplot.
        - margin: [0-1], figure margin (in proportion of figure)
        - figw_inch: float, figure width in inches (height is derived from width, in inches)
        - figh_inch: float, specify figure height instead of width
        - as_heatmap: bool, whether to display waveform as heatmap instead of collection of 2D plots
        - use_dsmatch: bool, whether to use drift-shift-matched waveform
        - verbose: bool, whether to print details
    Returns:
        - matplotlib figure with Nchannels subplots, plotting the mean
    '''

    # Get metadata
    saveDir=op.expanduser(saveDir)
    fs=read_metadata(dp)['highpass']['sampling_rate']
    pv=None if ignore_ks_chanfilt else 'local'
    cm=chan_map(dp, y_orig='tip', probe_version=pv)

    #peak_chan=get_peak_chan(dp, u, use_template=False, again=again) # use get_pc(waveforms)
    #peak_chan_i = int(np.argmin(np.abs(cm[:,0]-peak_chan)))
    t_waveforms_s=int(t_waveforms*(fs/1000))

    # Get data
    if not use_dsmatch:
        waveforms=wvf(dp, u=u, n_waveforms=n_waveforms, t_waveforms=t_waveforms_s, selection='regular',
                        periods=periods, spike_ids=spike_ids, wvf_batch_size=wvf_batch_size, ignore_nwvf=ignore_nwvf, verbose=verbose, again=again,
                        whiten=whiten, med_sub=med_sub, hpfilt=hpfilt, hpfiltf=hpfiltf, nRangeWhiten=nRangeWhiten, nRangeMedSub=nRangeMedSub,
                        ignore_ks_chanfilt = ignore_ks_chanfilt)
        assert waveforms.shape[0]!=0,'No waveforms were found in the provided periods!'
        assert waveforms.shape[1:]==(t_waveforms_s, cm.shape[0])
    else:
        plot_std=False
        sample_lines=0
        plot_debug=True if verbose else False
        waveforms=wvf_dsmatch(dp, u, n_waveforms=n_waveforms,
                  t_waveforms=t_waveforms_s, periods=periods,
                  wvf_batch_size=wvf_batch_size, ignore_nwvf=True, spike_ids = None,
                  save=True, verbose=verbose, again=again,
                  whiten=whiten, med_sub=med_sub, hpfilt=hpfilt, hpfiltf=hpfiltf,
                  nRangeWhiten=nRangeWhiten, nRangeMedSub=nRangeMedSub, plot_debug=plot_debug)[1]
    n_samples = waveforms.shape[-2]
    n_channels = waveforms.shape[-1]
    assert (n_samples, n_channels)==(t_waveforms_s, cm.shape[0])
    
    if not use_dsmatch:
        peak_chan_i = np.argmax(np.ptp(waveforms.mean(0), axis=0))
    else:
        peak_chan_i = np.argmax(np.ptp(waveforms, axis=0))

    # Filter the right channels
    if chStart is None:
        chStart_i = int(max(peak_chan_i-Nchannels//2, 0))
        chStart=cm[chStart_i,0]
    else:
        chStart_i = int(max(int(np.argmin(np.abs(cm[:,0]-chStart))), 0)) # finds closest chStart given kilosort chanmap
        chStart=cm[chStart_i,0] # Should remain the same, unless chStart was capped to 384 or is a channel ignored to kilosort

    chStart_i=int(min(chStart_i, n_channels-Nchannels-1))
    chEnd_i = int(chStart_i+Nchannels) # no lower capping needed as
    assert chEnd_i <= n_channels-1

    if not use_dsmatch:
        data = waveforms[:, :, chStart_i:chEnd_i]
        data=data[~np.isnan(data[:,0,0]),:,:] # filter out nan waveforms
        datam = np.mean(data,0)
        datastd = np.std(data,0)
    else:
        datam = waveforms[:, chStart_i:chEnd_i]
        data = datam # place holder
        datastd = datam*0
    subcm=cm[chStart_i:chEnd_i,:].copy().astype(np.float32)

    # eventually load templates
    if plot_templates:
        tplts=templates(dp, u, ignore_ks_chanfilt=ignore_ks_chanfilt)
        assert tplts.shape[2]==waveforms.shape[-1]==cm.shape[0]
        tplts=tplts[:, :, chStart_i:chEnd_i]
        x = np.linspace(0, n_samples/(fs/1000), n_samples) # Plot t datapoints between 0 and t/30 ms
        x_tplts = x[(n_samples-tplts.shape[1])//2:(n_samples-tplts.shape[1])//2+tplts.shape[1]] # Plot 82 datapoints between 0 and 82/30 ms
        tplt_chani_rel=peak_chan_i-chStart_i if chStart is None else np.argmax(np.max(datam, 1)-np.min(datam, 1))
    else:
        x_tplts = None
        tplts = None
        tplt_chani_rel = None

    # define a title
    if title is None:
        title = f"wvf {int(u)}@{int(cm[peak_chan_i, 0])}"

    return plt_wvf(data, subcm, datastd,
             x_tplts, tplts, tplt_chani_rel, fs,
             title, plot_std, plot_mean, plot_templates,
             color, labels, show_channels,
             scalebar_w, ticks_lw, sample_lines, ylim,
             saveDir, saveFig, saveData, _format,
             ax_edge_um_x, ax_edge_um_y, margin,
             figw_inch, figh_inch, as_heatmap)

def plt_wvf(waveforms, subcm=None, waveforms_std=None,
            x_tplts=None, tplts=None, tplt_chani_rel=None, fs=30000,
            title = None, plot_std=True, plot_mean=True, plot_templates=False,
            color='dodgerblue', labels=False, show_channels=True,
            scalebar_w=5, ticks_lw=1, sample_lines=0, ylim=[0,0],
             saveDir='~/Downloads', saveFig=False, saveData=False, _format='pdf',
             ax_edge_um_x=22, ax_edge_um_y=18, margin=0.12,
             figw_inch=6, figh_inch=None, as_heatmap=False):
    """
    Waveform plotting utility function.

    - waveforms: (n_waves, n_samples, n_channels) or (n_samples, n_channels) array, waveforms in uV
    - subcm: (n_channels, 3) or (n_channels, ) array ((channel_id, x, y) or (channel_id)), subset of channel map
    """
    # formatting parameters
    if isinstance(color, str):
        color=to_rgb(color)
    color_dark=(max(color[0]-0.08,0), max(color[1]-0.08,0), max(color[2]-0.08,0))

    if waveforms_std is None:
        plot_std=False
    else:
        waveforms_std = waveforms_std.T

    assert waveforms.ndim in [1,2,3],\
        'waveforms array shape wrong (should be (n_samples,), (n_waves, n_samples, n_channels) or (n_samples, n_channels))'
    if waveforms.ndim == 1:
        waveforms = waveforms[:,None]

    # formatting waveforms array
    if waveforms.ndim == 3:
        n_waveforms, n_samples, n_channels = waveforms.shape
        datam = waveforms.mean(0).T
        if type(sample_lines) is str:
            assert sample_lines=='all'
            sample_lines=min(waveforms.shape[0], n_waveforms)
        elif type(sample_lines) in [int, float]:
            sample_lines=min(waveforms.shape[0], sample_lines, n_waveforms)
    elif waveforms.ndim == 2:
        n_waveforms = 1
        n_samples, n_channels = waveforms.shape
        datam = waveforms.T
        sample_lines = 0
    
    # channels and channelmap
    if subcm is None:
        # make up channel map
        subcm=predefined_chanmap(probe_version='1.0')
        subcm = subcm[:n_channels,:]
    else:
        if subcm.ndim==1:
            subcm_madeup = predefined_chanmap(probe_version='1.0')
            subcm = np.vstack(subcm[:,None], subcm_madeup[:n_channels,1:])
    assert subcm.shape[0]==n_channels
    subcm = subcm.astype(np.float32)

    # find shared y limits
    if plot_std:
        datamin, datamax = np.nanmin(datam-waveforms_std)-50, np.nanmax(datam+waveforms_std)+50
    else:
        datamin, datamax = np.nanmin(datam)-50, np.nanmax(datam)+50
    ylim1, ylim2 = (datamin, datamax) if ylim==[0,0] else (ylim[0], ylim[1])
    x = np.linspace(0, datam.shape[1]/(fs/1000), datam.shape[1]) # Plot t datapoints between 0 and t/30 ms

    # Plot
    if as_heatmap:
        hm_yticks=get_bestticks_from_array(subcm[:,0], step=None)[::-1]
        hm_xticks=get_bestticks_from_array(x, step=None)
        if figh_inch is None: figh_inch=figw_inch/4+0.04*subcm.shape[0]
        fig=imshow_cbar(datam, origin='bottom', xevents_toplot=[], yevents_toplot=[], events_color='k', events_lw=2,
                xvalues=x, yvalues=subcm[::-1,0], xticks=hm_xticks, yticks=hm_yticks,
                xticklabels=hm_xticks, yticklabels=hm_yticks, xlabel='Time (ms)', ylabel='Channel', xtickrot=0, title=title,
                cmapstr="RdBu_r", vmin=ylim1*0.5, vmax=ylim2*0.5, center=0, colorseq='linear',
                clabel='Voltage (\u03bcV)', cticks=None,
                figsize=(figw_inch/2,figh_inch), aspect='auto', function='imshow',
                ax=None)
    else:
        # Initialize figure and subplots layout
        assert 0<=margin<1
        fig_hborder=[margin,1-margin] # proportion of figure used for plotting
        fig_wborder=[margin,1-margin] # proportion of figure used for plotting
        minx_um,maxx_um=min(subcm[:,1])-ax_edge_um_x/2, max(subcm[:,1])+ax_edge_um_x/2
        miny_um,maxy_um=min(subcm[:,2])-ax_edge_um_y/2, max(subcm[:,2])+ax_edge_um_y/2
        subcm[:,1]=((subcm[:,1]-minx_um)/(maxx_um-minx_um)*np.diff(fig_wborder)+fig_wborder[0]).round(2)
        subcm[:,2]=((subcm[:,2]-miny_um)/(maxy_um-miny_um)*np.diff(fig_hborder)+fig_hborder[0]).round(2)
    
        # i is the relative raw data /channel index (low is bottom channel)
        i_bottomleft=np.nonzero((subcm[:2,1]==min(subcm[:2,1]))&(subcm[:2,2]==min(subcm[:2,2])))[0]
        i_bottomleft=np.argmin(subcm[:2,2]) if i_bottomleft.shape[0]==0 else i_bottomleft[0]

        
        if figh_inch is None:
            figh_inch=figw_inch*(maxy_um-miny_um)/(maxx_um-minx_um)
        axw=(ax_edge_um_x/(maxx_um-minx_um)*np.diff(fig_wborder))[0] # in ratio of figure size
        axh=(ax_edge_um_y/(maxy_um-miny_um)*np.diff(fig_hborder))[0] # in ratio of figure size  

        fig=plt.figure(figsize=(figw_inch, figh_inch))
        ax=np.empty((n_channels), dtype='O')
        for i in range(n_channels):
            x0,y0 = subcm[i,1:]
            ax[i] =fig.add_axes([x0-axw/2,y0-axh/2,axw,axh], autoscale_on=False)

        # Plot on subplots
        for i in range(n_channels):
            for j in range(sample_lines):
                assert waveforms.ndim==3
                ax[i].plot(x, waveforms[j,:, i], linewidth=0.3, alpha=0.3, color=color)
            if plot_templates:
                tpl_scalings=[]
                for tpl in tplts:
                    num = max(datam[tplt_chani_rel, :])-min(datam[tplt_chani_rel, :])
                    denom = max(tpl[:,tplt_chani_rel])-min(tpl[:,tplt_chani_rel])
                    tpl_scalings.append(num/denom)
                if np.inf in tpl_scalings:
                    tpl_scalings[tpl_scalings==np.inf]=1
                    print('WARNING manually selected channel range does not comprise template (all zeros).')
                for tpl_i, tpl in enumerate(tplts):
                    ax[i].plot(x_tplts, tpl[:,i]*tpl_scalings[tpl_i], linewidth=1, color=(0,0,0), alpha=0.7, zorder=10000)
            if plot_mean:
                ax[i].plot(x, datam[i, :], linewidth=2, color=color_dark, alpha=1)
            if plot_std:
                ax[i].plot(x, datam[i, :]+waveforms_std[i,:], linewidth=1, color=color, alpha=0.5)
                ax[i].plot(x, datam[i, :]-waveforms_std[i,:], linewidth=1, color=color, alpha=0.5)
                ax[i].fill_between(x, datam[i, :]-waveforms_std[i,:], datam[i, :]+waveforms_std[i,:], facecolor=color, interpolate=True, alpha=0.2)
            ax[i].set_ylim([ylim1, ylim2])
            ax[i].set_xlim([x[0], x[-1]])
            ax[i].spines['right'].set_visible(False)
            ax[i].spines['top'].set_visible(False)
            ax[i].spines['left'].set_lw(ticks_lw)
            ax[i].spines['bottom'].set_lw(ticks_lw)
            if show_channels:
                ax[i].text(0.99, 0.99, int(subcm[i,0]),
                                size=12, weight='regular', ha='right', va='top', transform = ax[i].transAxes)
            if labels:
                ax[i].tick_params(axis='both', bottom=1, left=1, top=0, right=0, width=ticks_lw, length=3*ticks_lw, labelsize=12)
                if i==i_bottomleft:
                    ax[i].set_ylabel('Voltage (\u03bcV)', size=12, weight='bold')
                    ax[i].set_xlabel('Time (ms)', size=12, weight='bold')
                else:
                    ax[i].set_xticklabels([])
                    ax[i].set_yticklabels([])
            else:
                ax[i].axis('off')
        if not labels:
            xlimdiff=np.diff(ax[i_bottomleft].get_xlim())
            ylimdiff=ylim2-ylim1
            y_scale=int(ylimdiff*0.3-(ylimdiff*0.3)%10)
            ax[i_bottomleft].plot([0,1],[ylim1,ylim1], c='k', lw=scalebar_w)
            ax[i_bottomleft].text(0.5, ylim1-0.05*ylimdiff, '1 ms', weight='bold', size=18, va='top', ha='center')
            ax[i_bottomleft].plot([0,0],[ylim1,ylim1+y_scale], c='k', lw=scalebar_w)
            ax[i_bottomleft].text(-0.05*xlimdiff, ylim1+y_scale*0.5, f'{y_scale} \u03bcV', weight='bold', size=18, va='center', ha='right')
        if title is not None:
            fig.suptitle(t=title, x=0.5, y=0.92+0.02*(len(title.split('\n'))-1), size=18, weight='bold', va='top')

    # Save figure
    if title is None: title="waveforms"
    if saveFig:
        save_mpl_fig(fig, title, saveDir, _format)
    if saveData:
        save_np_array(waveforms, title, saveDir)

    return fig

def quickplot_n_waves(w, title='', peak_channel=None, nchans = 16,
                     fig=None, color=None, custom_text=None):
    "w is a (n_samples, n_channels) array"
    t = np.arange(-w.shape[0]//2/30, w.shape[0]//2/30, 1/30)
    if peak_channel is None:
        pk = np.argmax(np.ptp(w, axis=0))
    else:
        pk = peak_channel
    ylim = [np.min(w[:,pk])-50, np.max(w[:,pk])+50]
    if fig is None: fig = plt.figure(figsize=(3.5, 14))
    chans = np.arange(pk-nchans//2, pk+nchans//2)
    if custom_text is not None:
        assert isinstance(custom_text, list)
        assert len(custom_text) == nchans
    for i in range(nchans):
        ax = plt.subplot(nchans//2, 2, i+1) # will retrieve axes if alrady exists
        if chans[i] == pk:
            ax.spines['right'].set_color('red')
            ax.spines['left'].set_color('red')
            ax.spines['top'].set_color('red')
            ax.spines['bottom'].set_color('red')
        ax.text(0.05, 0.7, f'{chans[i]}', fontsize=8, transform = ax.transAxes)
        if custom_text is not None:
            ax.text(0.8, 0.7, str(custom_text[i]), fontsize=8, transform = ax.transAxes)
        ax.plot(t, w[:,chans[i]],
                alpha=0.8, lw=1, color=color)
        ax.set_ylim(ylim)
        ax.set_xlim([t[0], t[-1]])
        if i%2==1: ax.set_yticklabels([])
        if i<nchans-2: ax.set_xticklabels([])
    fig.suptitle(title, y=0.92)
    
    return fig

def plot_raw(dp, times=None, alignement_events=None, window=None, channels=np.arange(384), filt_key='highpass',
             offset=450, color='black', lw=1, bg_alpha=0.8,
             title=None, _format='pdf',  saveDir='~/Downloads', saveFig=0, figsize=(8,10), saveData=False, again=False,
             center_chans_on_0=True, whiten=False, med_sub=False, hpfilt=False, hpfiltf=300,
             nRangeWhiten=None, nRangeMedSub=None, use_ks_w_matrix=False, ignore_ks_chanfilt=True,
             filter_forward=True, filter_backward=True,
             plot_ylabels=True, show_allyticks=0, yticks_jump=None, plot_baselines=False,
             events=[], set0atEvent=1, align_events_as_sweeps=False,
             ax=None, ext_data=None, ext_datachans=np.arange(384),
             as_heatmap=False, vmin=-50, vmax=50, center=0, legend=None):
    '''
    Plot raw data over a specified window of time, over a specified range of channels.

    Arguments:
    - dp: binary path (files must ends in .bin, typically ap.bin)
    - times: list of boundaries of the time window, in seconds [t1, t2].
    - alignement_events: list of events to align the stimulus to compute an average, in seconds
    - window: [w1,w2], boundaries of mean raw trace if alignement_events is provides (ms) | Default: [-10,10]
    - channels (default: np.arange(0, 385)): list of channels of interest, in 0 indexed integers [c1, c2, c3...]
    - filt_key: 'highpass' or 'lowpass', whether to plot high or low pass filtered file (ap or lf)
    - offset: graphical offset between channels, in uV (ise to scale up/down in y)


    - color: color to plot all the lines ('multi' will use 20DistinctColors iteratively to distinguish channels by eye)
    - lw: float, linewidth of traces
    - bg_alpha: float [0-1], background alpha
    - title: str, figure title

    - saveDir: directory where to save either the figure or the data (default: ~/Downloads)
    - saveFig: save the figure at saveDir
    - _format: format of the figure to save | default: pdf
    - figsize: (x,y) tuple, size of figure in inches
    - saveData: bool, whether to save data used to make the plot (n_channels x time array, where time is in samples (30kHz))
    - again: bool, whether to recompute data rather than loading it from disc

    - center_chans_on_0: bool, whether to median subtract in time to reccenter channels on 0
    - whiten: whether to whiten the data across channels. If nRangeWhiten is not None, whitening matrix is computed with the nRangeWhiten closest channels.
    - med_sub: whether to median-subtract the data across channels. If nRangeMedSub is not none, median of each channel is computed using the nRangeMedSub closest channels.
    - hpfilt: whether to high-pass filter the data, using a 3 nodes butterworth filter of cutoff frequency hpfiltf.
    - hpfiltf: see hpfilt
    - nRangeWhiten: int, see whiten.
    - nRangeMedSub: int, see med_sub.
    - use_ks_w_matrix: bool, whether to use kilosort's original whitening matrix to perform the whitening
                     (rather than recomputing it from the data at hand)
    - ignore_ks_chanfilt: whether to ignore the filtering made by kilosort,
                          which only uses channels with average events rate > ops.minfr to spike sort.

    - plot_ylabels: bool, whether to plot y labels
    - show_allyticks: bool, whetehr to show all y ticks or not (every 50uV for each individual channel),
                      only use if exporing data
    - yticks_jump: int, plot ytick label every yticks_jump ticks
    - plot_baselines: bool, whether to plot dotted lines at 0 for every channel

    - events: list of times where to plot vertical lines, in seconds.
    - set0atEvent: boolean, set time=0 as the time of the first event provided in the list events, if any is provided.
    - ax: matplotlib axes, where plot will be plotted if provided
    - ext_data: array of shape (N channels, N time samples), externally porovided data to plot
    - ext_datachans: array matching the number of channels of ext_data to plot the proper y labels

    - as_heatmap: whether to plot data as heatmap rather than 2D lines
    - vmin, vmax, center: float, values of heatmap colorbar

    Returns:
    - fig: a matplotlib figure with channel 0 being plotted at the bottom and channel 384 at the top.

    '''
    assert filt_key in ['highpass', 'lowpass']
    fs = read_metadata(dp)[filt_key]['sampling_rate']
    assert assert_iterable(events)
    # Get data
    if ext_data is None:
        channels=assert_chan_in_dataset(dp, channels, ignore_ks_chanfilt)
        if times is not None:
            assert alignement_events is None, 'You can either provide a window of 2 times or a list of alignement_events \
                + a single window to compute an average, but not both!'
            rc = extract_rawChunk(dp, times, channels, filt_key, 1,
                     whiten, med_sub, hpfilt, hpfiltf, filter_forward, filter_backward,
                     nRangeWhiten, nRangeMedSub, use_ks_w_matrix,
                     ignore_ks_chanfilt, center_chans_on_0, 0, 1, again)

        if alignement_events is not None:
            assert window is not None
            window[1]=window[1]+1*1000/fs # to make actual window[1] tick visible
            assert times is None, 'You can either provide a window of 2 times or a list of alignement_events \
                + a single window to compute an average, but not both!'
            assert len(alignement_events)>=1, "You must provide a list/array of alignement_events!"
            rc=extract_rawChunk(dp, alignement_events[0]+npa(window)/1e3, channels, filt_key, 1,
                     whiten, med_sub, hpfilt, hpfiltf, filter_forward, filter_backward,
                     nRangeWhiten, nRangeMedSub, use_ks_w_matrix,
                     ignore_ks_chanfilt, center_chans_on_0, 0, 1, again)
            for e in alignement_events[1:]:
                times=e+npa(window)/1e3
                if align_events_as_sweeps:
                    rc = np.concatenate((rc, extract_rawChunk(dp, times, channels, filt_key, 1,
                                                              whiten, med_sub, hpfilt, hpfiltf, filter_forward,
                                                              filter_backward, nRangeWhiten, nRangeMedSub,
                                                              use_ks_w_matrix, ignore_ks_chanfilt,
                                                              center_chans_on_0, 0, 1, again)))
                else:
                    rc += extract_rawChunk(dp, times, channels, filt_key, 1,
                                         whiten, med_sub, hpfilt, hpfiltf, filter_forward, filter_backward,
                                         nRangeWhiten, nRangeMedSub, use_ks_w_matrix,
                                         ignore_ks_chanfilt, center_chans_on_0, 0, 1, again)
            rc = rc/len(alignement_events) if not align_events_as_sweeps else rc
    else:
        channels=assert_chan_in_dataset(dp, ext_datachans, ignore_ks_chanfilt)
        assert len(channels)==ext_data.shape[0],\
            f"ext_data is of shape {ext_data.shape} but {len(channels)} channels are expected."
        assert window is not None, 'You must tell the plotting function to which time window the external data corresponds to!'
        times=window
        rc=ext_data.copy()

    # Define y ticks
    plt_offsets = np.arange(0, rc.shape[0]*offset, offset)
    y_ticks = np.arange(0, rc.shape[0], 1) if as_heatmap else np.arange(0, rc.shape[0]*offset, offset)
    y_ticks_labels = np.repeat(np.asarray(alignement_events), len(channels)) if align_events_as_sweeps else channels

    # Sparsen y tick labels to declutter y axis
    if not show_allyticks:
        if yticks_jump is None:
            yticks_jump = get_bestticks(0, len(y_ticks_labels))
            yticks_jump = yticks_jump[1] - yticks_jump[0]
        y_ticks_labels=y_ticks_labels[np.arange(len(y_ticks))%yticks_jump==0]
        y_ticks=y_ticks[np.arange(len(y_ticks))%yticks_jump==0]

    # Plot data
    t=np.arange(rc.shape[1])*1000./fs # in milliseconds
    if any(events) and times is not None:
        events=[e-times[0] for e in events] # offset to times[0]
        if set0atEvent:
            t=t-events[0]*1000
            events=[e-events[0] for e in events]
    if alignement_events is not None:
        t=t+window[0]
        events=[0]

    if isinstance(color, str):
        if color=='multi':color=None
        else:color=to_rgb(color)
    if as_heatmap:
        xticklabels = get_bestticks_from_array(t, step=None)
        xticks=xticklabels*fs/1000
        y_ticks_labels=npa([x*10 if x%2==0 else x*10-10 for x in y_ticks_labels])

        fig=imshow_cbar(im=rc, origin='top', xevents_toplot=[], events_color='k',
                        xvalues=None, yvalues=None, xticks=xticks-xticks[0], yticks=y_ticks,
                        xticklabels=xticklabels, yticklabels=y_ticks_labels, xlabel=None, ylabel=None,
                        cmapstr="RdBu_r", vmin=vmin, vmax=vmax, center=center, colorseq='nonlinear',
                        clabel='Voltage (\u03BCV)', cticks=None,
                        figsize=(4,10), aspect='auto', function='imshow', ax=None)
        ax=fig.axes[0]
        ax.set_ylabel('Depth (\u03BCm)', size=14, weight='bold')
    else:
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = ax.get_figure()
        t=np.tile(t, (rc.shape[0], 1))
        rc+=plt_offsets[:,np.newaxis]
        if plot_baselines:
            for i in np.arange(rc.shape[0]):
                y=i*offset
                ax.plot([t[0,0], t[0,-1]], [y, y], color=(0.5, 0.5, 0.5), linestyle='--', linewidth=1)
        ax.plot(t.T, rc.T, linewidth=lw, color=color, alpha=bg_alpha)
        ax.plot(t[:,0], rc[:,0], color=color, alpha=bg_alpha,  label=legend)
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_ticks_labels) if plot_ylabels else ax.set_yticklabels([])
        if align_events_as_sweeps:
            ax.set_ylabel('Event (s)', size=14, weight='bold')
        else:
            ax.set_ylabel('Channel', size=14, weight='bold')

    ax.set_xlabel('Time (ms)', size=14, weight='bold')
    ax.tick_params(axis='both', bottom=1, left=1, top=0, right=0, width=2, length=6, labelsize=14)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_lw(2)
    ax.spines['bottom'].set_lw(2)

    if title is not None: ax.set_title(title, size=20, weight='bold', va='bottom')

    yl=ax.get_ylim() if as_heatmap else [np.min(rc[0,:])-offset,np.max(rc[-1,:])+offset]
    xl=[0, (t[-1]-t[0])*fs/1000] if as_heatmap else [t[0,0], t[0,-1]]
    for e in events:
        if as_heatmap: e=(e-t[0])*(fs/1000)
        ax.plot([e,e], yl, color=(0.3, 0.3, 0.3), linestyle='--', linewidth=1.5)
    ax.set_ylim(yl)
    ax.set_xlim(xl)

    if legend is not None:
        plt.legend(bbox_to_anchor = (1,1,0,0), fontsize=14, frameon=False)


    rcn = '{}_t{}-{}_ch{}-{}'.format(op.basename(dp), times[0], times[1], channels[0], channels[-1]) # raw chunk name
    rcn=rcn+'_whitened' if whiten else rcn+'_raw'
    if saveFig:
        if title is not None: rcn=title

        save_mpl_fig(fig, rcn, saveDir, _format)

    if saveData:
        save_np_array(rc, rcn, saveDir)

    return fig

def plot_raw_units(dp, times, units=[], channels=np.arange(384), offset=450,
                   Nchan_plot=5, spk_window=82, colors='phy', bg_color='k', lw=1, bg_alpha=0.8, lw_color=1.1,
                   title=None, saveDir='~/Downloads', saveData=0, saveFig=0, _format='pdf', figsize=(20,8),
                   whiten=False, nRangeWhiten=None, med_sub=False, nRangeMedSub=None, hpfilt=0, hpfiltf=300,
                   filter_forward=False, filter_backward=False,ignore_ks_chanfilt=0,
                   show_allyticks=0, yticks_jump=None, plot_ylabels=True, events=[], set0atEvent=1,
                   again=False, ax=None):
    f'''
    Plot raw traces with colored overlaid spike times of specified units.

    Arguments:
    - most parameters from plot_raw (see below)
    - units: list/array of units (if they do not spike within 'times', will be ignored)
    - Nchan_plot: int, number of channels over which to plot colored unit spikes
    - spk_window: int, width of plotted unit spikes (in samples)
    - colors: list of colors, same length as 'units' (or 'phy' to use phy colorscheme)
    - bg_color: str, color of background raw traces

    Returns:
    - fig: a matplotlib figure with channel 0 being plotted at the bottom and channel 384 at the top.

    plot_raw docstring:
    {plot_raw.__doc__}
    '''
    pyqtgraph=0
    # if channels is None:
    #     peakChan=get_peak_chan(dp,units[0])
    #     channels=np.arange(peakChan-Nchan_plot//2-1, peakChan+Nchan_plot//2+2)
    channels=assert_chan_in_dataset(dp, channels, ignore_ks_chanfilt)

    rc = extract_rawChunk(dp, times, channels, 'highpass', saveData,
                     whiten, med_sub, hpfilt, hpfiltf, filter_forward, filter_backward,
                     nRangeWhiten, nRangeMedSub, False,
                     ignore_ks_chanfilt, True, 0, 1, again)

    # Offset data
    plt_offsets = np.arange(0, len(channels)*offset, offset)
    plt_offsets = np.tile(plt_offsets[:,np.newaxis], (1, rc.shape[1]))
    rc+=plt_offsets

    fig=plot_raw(dp, times, None, None, channels, filt_key='highpass',
             offset=offset, color=bg_color, lw=lw, bg_alpha=bg_alpha,
             title=title, _format='pdf',  saveDir=saveDir, saveFig=0, figsize=figsize, again=False,
             center_chans_on_0=True, whiten=whiten, med_sub=med_sub, hpfilt=hpfilt, hpfiltf=hpfiltf,
             nRangeWhiten=nRangeWhiten, nRangeMedSub=nRangeMedSub, use_ks_w_matrix=False, ignore_ks_chanfilt=ignore_ks_chanfilt,
             filter_forward=filter_forward, filter_backward=filter_backward,
             plot_ylabels=plot_ylabels, show_allyticks=show_allyticks, yticks_jump=yticks_jump, plot_baselines=False,
             events=events, set0atEvent=set0atEvent,
             ax=ax, ext_data=None, ext_datachans=np.arange(384),
             as_heatmap=False, vmin=-50,vmax=50,center=0)
        

    if ax is None:
        ax=fig.get_axes()[0]
    assert assert_iterable(units)
    assert len(units)>=1
    fs=read_metadata(dp)['highpass']['sampling_rate']
    spk_w1 = spk_window // 2
    spk_w2 = spk_window - spk_w1
    t1, t2 = int(np.round(times[0]*fs)), int(np.round(times[1]*fs))

    if isinstance(colors, str):
        assert colors=='phy', 'You can only use phy as colors palette keyword.'
        phy_c=list(phyColorsDic.values())[:-1]
        colors=[phy_c[ci%len(phy_c)] for ci in range(len(units))]
    else:
        colors=list(colors)
        assert len(colors)==len(units), 'The length of the list of colors should be the same as the list of units!!'
        for ic, c in enumerate(colors):
            if isinstance(c, str): colors[ic]=to_rgb(c)

    tx=np.tile(np.arange(rc.shape[1]), (rc.shape[0], 1))[0] # in samples
    tx_ms=np.tile(np.arange(rc.shape[1])*1000./fs, (rc.shape[0], 1)) # in ms
    if any(events):
        events=[e-times[0] for e in events] # offset to times[0]
        if set0atEvent:
            tx_ms=tx_ms-events[0]*1000
            events=[e-events[0] for e in events]

    for iu, u in enumerate(units):
        print('plotting unit {}...'.format(u))
        peakChan=get_peak_chan(dp,u, use_template=True)
        assert peakChan in channels, "WARNING the peak channel of {}, {}, is not in the set of channels plotted here!".format(u, peakChan)
        peakChan_rel=np.nonzero(peakChan==channels)[0][0]
        ch1, ch2 = max(0,peakChan_rel-Nchan_plot//2), min(rc.shape[0], peakChan_rel-Nchan_plot//2+Nchan_plot)
        t=trn(dp,u) # in samples
        twin=t[(t>t1+spk_w1)&(t<t2-spk_w2)] # get spikes starting minimum spk_w1 after window start and ending maximum spk_w2 before window end
        twin-=t1 # set t1 as time 0
        for t_spki, t_spk in enumerate(twin):
            print('plotting spike {}/{}...'.format(t_spki+1, len(twin)), end='  ')
            spk_id=(tx>=t_spk-spk_w1)&(tx<=t_spk+spk_w2)
            if pyqtgraph:
                win,p = fig
                for line in np.arange(ch1, ch2, 1):
                    p.plot(tx_ms[line, spk_id].T, rc[line, spk_id].T, linewidth=1, pen=tuple(npa(colors[iu])*255))
                fig = win,p
            else:
                ax.plot(tx_ms[ch1:ch2, spk_id].T, rc[ch1:ch2, spk_id].T, lw=lw_color, color=colors[iu])
                #ax.plot(tx_ms[peakChan_rel, spk_id].T, rc[peakChan_rel, spk_id].T, lw=1.5, color=color)
                fig.tight_layout()
        print("\n")

    ax.set_ylim([-offset, rc.max()+offset/2])

    if saveFig:
        rcn = '{}_{}_t{}-{}_ch{}-{}'.format(op.basename(dp), list(units), times[0], times[1], channels[0], channels[-1]) # raw chunk name
        rcn=rcn+'_whitened' if whiten else rcn+'_raw'
        if title is not None: rcn=title
        save_mpl_fig(fig, rcn, saveDir, _format)

    return fig

#%% Peri-event plots ##############################################################################################

def psth_popsync_plot(trains, events, psthb=10, window=[-1000,1000],
                        events_tiling_frac=0.1, sync_win=2, fs=30000, t_end=None,
                        b=1, sd=1000, th=0.02,
                        again=False, dp=None, U=None,

                        zscore=False, zscoretype='within',
                        convolve=False, gsd=1, method='gaussian',
                        bsl_subtract=False, bsl_window=[-4000, 0], process_y=False,

                        events_toplot=[0], events_color='r',
                        title='', color='darkgreen', figsize=None,
                        saveDir='~/Downloads', saveFig=0, _format='pdf',
                        xticks=None, xticklabels=None, xlabel='Time (ms)', ylim=None, ax=None):

    x, y, y_p, y_p_var=get_processed_popsync(trains, events, psthb, window,
                          events_tiling_frac, sync_win, fs, t_end,
                          b, sd, th,
                          again, dp, U,
                          zscore, zscoretype,
                          convolve, gsd, method,
                          bsl_subtract, bsl_window, process_y)

    ylabel='Population synchrony\n(zscore of fraction firing)' if zscore \
        else r'$\Delta$ pop synchrony\n(fraction firing)' if bsl_subtract else 'Population synchrony\n(fraction firing)'
    return psth_plt(x, y_p, y_p_var, window, events_toplot, events_color,
           title, color,
           saveDir, saveFig, _format,
           zscore, bsl_subtract, ylim,
           convolve, xticks, xticklabels, xlabel, ylabel, None, False,
           ax, figsize)

def psth_plot(times, events, psthb=5, psthw=[-1000, 1000], remove_empty_trials=True, events_toplot=[0], events_color='r',
           title='', color='darkgreen', legend_label=None, legend=False,
           saveDir='~/Downloads', saveFig=0, ret_data=0, _format='pdf',
           zscore=False, bsl_subtract=False, bsl_window=[-2000,-1000], ylim=None,
           convolve=True, gsd=2, xticks=None, xticklabels=None, xlabel='Time (ms)', ylabel=None,
           ax=None, figsize=None, tight_layout=True, hspace=None, wspace=None, prettify=True, **mplp_kwargs):

    x, y, y_p, y_p_var = get_processed_ifr(times, events, b=psthb, window=psthw, remove_empty_trials=remove_empty_trials,
                                      zscore=zscore, zscoretype='within',
                                      convolve=convolve, gsd=gsd, method='gaussian_causal',
                                      bsl_subtract=bsl_subtract, bsl_window=bsl_window)

    fig = psth_plt(x, y_p, y_p_var, psthw, events_toplot, events_color,
           title, color,
           saveDir, saveFig, _format,
           zscore, bsl_subtract, ylim,
           convolve, xticks, xticklabels,
           xlabel, ylabel, legend_label, legend,
           ax, figsize, tight_layout, hspace, wspace, prettify, **mplp_kwargs)

    return (x,y,y_p,y_p_var) if ret_data else fig

def psth_plt(x, y_p, y_p_var, psthw, events_toplot=[0], events_color='r',
           title='', color='darkgreen',
           saveDir='~/Downloads', saveFig=0, _format='pdf',
           zscore=False, bsl_subtract=False, ylim=None,
           convolve=True, xticks=None, xticklabels=None,
           xlabel='Time (ms)', ylabel='IFR (spk/s)', legend_label=None, legend=False,
           ax=None, figsize=None, tight_layout=True, hspace=None, wspace=None,
           prettify=True, **mplp_kwargs):
    """
    Plots peri-event PSTHs
    Arguments:
        - x: time vector
        - y_p: mean PSTH
        - y_p_var: std of PSTH
        - psthw: peri-stimulus time window
        - events_toplot: list of event indices to plot
        - events_color: color of event lines
        - title: plot title
        - color: color of PSTH
        - saveDir: directory to save figure
        - saveFig: bool, whether to save figure or not
        - _format: format to save figure in
        - zscore: bool, PSTH was zscored or not
        - bsl_subtract: bool, whether to subtract baseline from PSTH or not
        - ylim: y-axis limits
        - convolve: bool, whether PSTH was convolved or not
        - xticks: x-axis ticks
        - xticklabels: x-axis tick labels
        - xlabel: x-axis label
        - ylabel: y-axis label
        - legend_label: label for legend
        - legend: bool, whether to plot legend or not
        - ax: axis to plot on
        - figsize: figure size
        - tight_layout: bool, whether to apply tight_layout() or not
        - hspace: horizontal space between subplots
        - wspace: vertical space between subplots
        - prettify: bool, whether to apply mplp() prettification or not
        - **mplp_kwargs: any additional formatting parameters, passed to mplp()
    """
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig=ax.get_figure()

    areasteps=None if convolve else 'post'

    if zscore or bsl_subtract:
        ax.fill_between(x, y_p-y_p_var, y_p+y_p_var,
                        color=color, alpha=0.8, step=areasteps, label=legend_label)
    else:
        ax.fill_between(x, y_p-y_p_var, y_p+y_p_var, color=color, alpha=0.5, step=areasteps)
        ax.fill_between(x, y_p*0, y_p,
                        color=color, alpha=1, step=areasteps, label=legend_label)
    if legend: ax.legend()
    if convolve:
        if zscore or bsl_subtract: ax.plot(x, y_p-y_p_var, color='black', lw=0.5)
        ax.plot(x, y_p+y_p_var, color='black', lw=0.5)
        ax.plot(x, y_p, color='black', lw=2)
    else:
        if zscore or bsl_subtract: ax.step(x, y_p-y_p_var, color='black', lw=0.5, where='post')
        ax.step(x, y_p+y_p_var, color='black', lw=0.5, where='post')
        ax.step(x, y_p, color='black', lw=2,where='post')

    yl=ax.get_ylim() if ylim is None else ylim
    assert assert_iterable(yl), 'WARNING the provided ylim need to be of format [ylim1, ylim2]!'
    if not (zscore or bsl_subtract): yl=[0,yl[1]]
    for etp in events_toplot:
        ax.plot([etp,etp], yl, ls='--', lw=1, c=events_color)
        ax.set_ylim(yl)

    xl=psthw
    if bsl_subtract or zscore:
        ax.plot(xl,[0,0],lw=1,ls='--',c='black',zorder=-1)
        if zscore:
            if yl[0]<-2: ax.plot(xl,[-2,-2],lw=1,ls='--',c='black',zorder=-1)
            if yl[1]>2: ax.plot(xl,[2,2],lw=1,ls='--',c='black',zorder=-1)
    ax.set_xlim(xl)

    if ylabel is None:
        ylabel='IFR\n(zscore)' if zscore else r'$\Delta$ FR (spk/s)' if bsl_subtract else 'IFR (spk/s)'
    if xlabel is None: xlabel=''

    fig,ax=mplp(fig=fig, ax=ax, figsize=figsize,
     xlim=psthw, ylim=yl, xlabel=xlabel, ylabel=ylabel,
     xticks=xticks, xtickslabels=xticklabels,
     axlab_w='bold', axlab_s=16,
     ticklab_w='regular',ticklab_s=14, lw=1,
     title=title, title_w='bold', title_s=16,
     hide_top_right=True, tight_layout=tight_layout, hspace=hspace, wspace=wspace,
     prettify=prettify, **mplp_kwargs)

    if saveFig:
        figname=title
        save_mpl_fig(fig, figname, saveDir, _format)

    return fig

def raster_plot(times, events, window=[-1000, 1000], events_toplot=[0], events_color='r',
                trials_toplot=[], remove_empty_trials=False,
                title='', color='darkgreen', palette='batlow',
                marker='|', malpha=0.9, size=None, lw=3, sparseylabels=True, figsize=None,
                saveDir='~/Downloads', saveFig=0, ret_data=0, _format='pdf',
                as_heatmap=False, vmin=None, center=None, vmax=None, cmap_str=None,
                show_psth=False, psthb=10,
                zscore=False, bsl_subtract=False, bsl_window=[-2000,-1000], ylim_psth=None,
                convolve=True, gsd=2, prettify=True, **mplp_kwargs):
    '''
    Make a raster plot of the provided 'times' aligned on the provided 'events', from window[0] to window[1].
    By default, there will be len(events) lines. you can pick a subset of events to plot
    by providing their indices as a list.array with 'events_toplot'.

    Arguments:
        - times: list/array of spike times, in seconds. If list of lists/arrays,
                 each item of the list is considered an individual spike train.
        - events: list/array of events, in seconds. TRIALS WILL BE PLOTTED ACORDING TO EVENTS ORDER.
        - window: list/array of shape (2,): the raster will be plotted from events-window[0] to events-window[1] | Default: [-1000,1000]
        - events_toplot: list/array of events indices to display on the raster | Default: None (plots everything)
        - events_color: string or list of strings of same size as events_toplot (in cases of several events)
        - trials_toplot: list/array of trials indices to display on the raster | Default: None (plots everything)
        - remove_empty_trials: boolean, if True does not use empty trials to compute psth

        - title: string, title of the plot + if saved file name will be raster_title._format.
        - color: string or list of strings of same length as 'times' (in cases of several cells)
        - palette: string, name of the color palette to use instead of directly passing colors | Default: 'batlow'
        - marker: string, marker to use for the raster | Default: '|'
        - malpha: float, opacity for the raster | Default: 0.9
        - size: float, size of the raster | Default: None (uses lw)
        - lw: float, line width of the raster | Default: 3
        - sparseylabels: boolean, if True, only displays ylabels for the first and last trials | Default: True

        - figsize: tuple, (x,y) figure size in inches
        - saveDir: save directory to save data and figure
        - saveFig: boolean, if 1 saves figure with name raster_title._format at saveDir
        - ret_data: boolean, whether to return data (x,y,y_p,y_p_var) instead of matplotlib figure.
        - _format: string, format used to save figure if saveFig=1 | Default: 'pdf'

        - as_heatmap: boolean, if True, plots a heatmap instead of a raster | Default: False
        - vmin: float, minimum value for the heatmap | Default: None (uses min of data)
        - center: float, center value for the heatmap | Default: None (uses mean of data)
        - vmax: float, maximum value for the heatmap | Default: None (uses max of data)
        - cmap_str: string, name of the colormap to use | Default: None (uses 'viridis' if as_heatmap else 'Greys')

        - show_psth: boolean, if True, plots a psth below the raster | Default: False
        - psthb: float, bin size for the psth | Default: 10
        - zscore: boolean, if True, zscores the psth | Default: False
        - bsl_subtract: boolean, if True, subtracts the baseline from the psth | Default: False
        - bsl_window: list/array of shape (2,): baseline window for the psth | Default: [-2000,-1000]
        - ylim_psth: list/array of shape (2,): y limits for the psth | Default: None (uses min/max of data)
        - convolve: boolean, if True, convolves the psth with a gaussian kernel | Default: True
        - gsd: float, gaussian standard deviation for the psth | Default: 2

        - prettify: bool, whether to apply mplp() prettification or not
        - **mplp_kwargs: any additional formatting parameters, passed to mplp()

    Returns:
        - fig: matplotlib figure.
    '''

    events_order=np.argsort(events)
    events=np.sort(events)

    n_cells=len(times) if isinstance(times[0], np.ndarray) else 1
    if n_cells==1: times=[times]
    print(f'{n_cells} cell(s) detected.')
    if isinstance(color, str):
        if n_cells==1: color=[color]
        else: color=get_ncolors_cmap(n_cells, palette, plot=False)
    else: assert len(color)==n_cells,\
        'WARNING the number of colors needs to match the number of cells provided (use [[r,g,b]] for 1 neuron)!'
    subplots_ratio=[4*n_cells,n_cells]

    if show_psth:
        grid = plt.GridSpec(sum(subplots_ratio), 1, wspace=0.2, hspace=0.2)
        fig = plt.figure()
        ax=fig.add_subplot(grid[:-n_cells, :])
    else:
        fig, ax = plt.subplots()


    # Define y ticks according to n_cells and trials order
    y_ticks=np.arange(len(events)*n_cells)+1
    y_ticks_labels=(np.arange(len(events)))[events_order]
    y_ticks_labels=np.hstack([y_ticks_labels[np.newaxis, :].T for i in range(n_cells)]).ravel()

    # Sparsen y tick labels to declutter y axis
    wrong_order=np.all(events_order==np.arange(events_order.shape[0]))
    if wrong_order: print('Events provided not sorted by time - this might be voluntary, just letting you know.')
    if sparseylabels and wrong_order:
        y_ticks_labels_sparse=[]
        for yi,yt in enumerate(y_ticks_labels):
            if yi%(5*n_cells)==0:y_ticks_labels_sparse.append(yt)
            else:y_ticks_labels_sparse.append('')
        y_ticks_labels=y_ticks_labels_sparse
    elif n_cells>1:
        y_ticks_labels_sparse=[]
        for yi,yt in enumerate(y_ticks_labels):
            if yi%(n_cells)==0:y_ticks_labels_sparse.append(yt)
            else:y_ticks_labels_sparse.append('')
        y_ticks_labels=y_ticks_labels_sparse

    # Plot raster
    if size is None: size=max(10,5400//len(events)) # 180 for 30 events
    if show_psth:size-=30; size=max(size,10)
    if title == '':
        title='raster' if not as_heatmap else 'heatmap'
    xlabel='Time (ms)'
    xticks=get_bestticks_from_array(np.arange(window[0], window[1], psthb), light=1)
    xlabel_plot=xlabel if not show_psth else None
    if figsize is None: figsize=[5,subplots_ratio[0]*2]
    if show_psth: figsize=[figsize[0], figsize[1]+figsize[1]//subplots_ratio[0]]
    for ci in range(n_cells):
        if as_heatmap:
            x, y, y_p, y_p_var = get_processed_ifr(times[ci], events, b=psthb, window=window, remove_empty_trials=remove_empty_trials,
                                      zscore=zscore, zscoretype='within',
                                      convolve=convolve, gsd=gsd, method='gaussian_causal',
                                      bsl_subtract=bsl_subtract, bsl_window=bsl_window, process_y=True)
            extremum=max(abs(0.9*y.min()),abs(0.9*y.max()))
            if vmin is None: vmin = 0 if not (zscore|bsl_subtract) else -extremum
            if vmax is None: vmax = 0.8*y.max() if not (zscore|bsl_subtract) else extremum
            if center is None:
                center=vmin+((vmax-vmin)/2)
            if cmap_str is None: cmap_str = 'viridis' if not (zscore|bsl_subtract) else 'RdBu_r'
            ntrials=y.shape[0]
            clab='Inst. firing rate (spk/s)' if not zscore else 'Inst. firing rate (zscore)'
            imshow_cbar(y, origin='top', xevents_toplot=events_toplot, events_color=events_color,
                        xvalues=np.arange(window[0], window[1], psthb), yvalues=np.arange(ntrials)+1,
                        xticks=xticks, yticks=y_ticks,
                        xticklabels=None, yticklabels=y_ticks_labels, xlabel=xlabel_plot, ylabel='Trials', title=title,
                        cmapstr=cmap_str, vmin=vmin, vmax=vmax, center=center, colorseq='nonlinear',
                        clabel=clab, cticks=None,
                        figsize=figsize, aspect='auto', function='imshow', ax=ax)

        else:
            at, atb = align_times(times[ci], events, window=window, remove_empty_trials=remove_empty_trials)
            ntrials=len(at)
            col=color if n_cells==1 else color[ci]
            for e, ts in at.items():
                i=events_order[np.nonzero(e==events)[0][0]]
                y=[y_ticks[i*n_cells+ci]]*len(ts)
                ts=npa(ts)*1000 # convert to ms
                ax.scatter(ts, y, s=size, color=col, alpha=malpha, marker=marker, lw=lw)
            fig,ax=mplp(fig=fig, ax=ax, figsize=figsize,
                 xlim=window, ylim=[y_ticks[-1]+1, 0], xlabel=xlabel_plot, ylabel="Trials",
                 xticks=xticks, yticks=y_ticks, xtickslabels=None, ytickslabels=y_ticks_labels,
                 axlab_w='bold', axlab_s=20,
                 ticklab_w='regular',ticklab_s=16, lw=1,
                 title=title, title_w='bold', title_s=24,
                 hide_top_right=True, hide_axis=False,
                 prettify=prettify, **mplp_kwargs)
    print(f'{ntrials} trials.')
    xl=ax.get_xlim()
    yl=ax.get_ylim()
    for etp in events_toplot:
        ax.plot([etp,etp], yl, ls='--', lw=1, color=events_color)
    if any(trials_toplot):
        for ttp in trials_toplot:
            ax.plot(xl, [ttp,ttp], ls='--', lw=1, color='k')
    ax.set_ylim(yl)
    ax.set_xlim(xl)

    if show_psth:
        xticks=ax.get_xticks()
        xticklabels=get_labels_from_ticks(xticks)[0]
        ax.set_xticklabels([])
        for ci in range(n_cells):
            ax_psth=fig.add_subplot(grid[-n_cells+ci, :])
            xticklabels_subplot=xticklabels if ci==n_cells-1 else ['' for i in xticklabels]
            xlabel_subplot=xlabel if ci==n_cells-1 else ''
            psth_plot(times[ci], events, psthb=psthb, psthw=window,
                      remove_empty_trials=remove_empty_trials, events_toplot=events_toplot, events_color=events_color,
                       title=None, color=color[ci], legend_label=None, legend=False,
                       saveDir=saveDir, saveFig=0, ret_data=0, _format='pdf',
                       zscore=zscore, bsl_subtract=bsl_subtract, bsl_window=bsl_window, ylim=ylim_psth,
                       convolve=convolve, gsd=gsd,
                       xticks=xticks, xticklabels=xticklabels_subplot, xlabel=xlabel_subplot, ylabel=None,
                       ax=ax_psth, figsize=None, tight_layout=True, hspace=None, wspace=None,
                       prettify=True, **mplp_kwargs)

    if saveFig:
        figname=title
        save_mpl_fig(fig, figname, saveDir, _format)

    return (x,y,y_p,y_p_var) if ret_data else fig

def summary_psth(trains, trains_str, events, events_str, psthb=5, psthw=[-1000,1000],
                 zscore=False, bsl_subtract=False, bsl_window=[-2000,-1000], convolve=True, gsd=2,
                 events_toplot=[0], events_col=None, trains_col_groups=None, overlap_events=False,
                 title=None, saveFig=0, saveDir='~/Downloads', _format='pdf',
                 figh=None, figratio=None, transpose=False, ylim=None,
                 as_heatmap=False,  vmin=None, center=None, vmax=None, cmap_str=None):
    '''
    Function to plot a bunch of PSTHs, all trains aligned to all sets of events, in a single summary figure.

    Arguments:
        Related to PSTH data:
            - trains: list of np arrays (s), spike trains
            - trains_str: list of str, name of trains units
            - events: list of np arrays (s), sets of events
            - events_str: list of str, name of event types
            - psthb: float (ms), psth binsize | Default 5
            - psthw: list of floats [w1,w2] (ms), psth window | Default [-1000,1000]
        Related to data processing:
            - zscore: bool, whether to zscore the data (mean/std calculated in bsl_window) | Default False
            - bsl_subtract: bool, whether to baseline_subtract | Default False
            - bsl_window: list of floats [w1,w2], window used to compute mean and std for zscoring | Default [-2000,-1000]
            - convolve: bool, whether to convolve the data with a causal gaussian window | Default True
            - gsd: float (ms), std of causal gaussian window | Default 2
        Related to events coloring/display:
            - events_toplot: list of floats, times at which to draw a vertical line | Default [0]
            - events_col: list of str/(r,g,b)/hex strings of len n_events, color of PSTHs (1 per event)
                          or str, matplotlib / crameri colormap | Default None
            - trains_col_groups: list of int of len n_trains, groups of units which should be colored alike | Default None
            - overlap_events: whether to overlap PSTHs across events. If True, it is advised to also use events_col to distinguish events properly.
        Related to figure saving:
            - title: str, figure suptitle also used as filename if saveFig is True | Default None
            - saveFig: bool, whether to save figure as saveDir/title._format | Default 0
            - saveDir: str, path to directory to save figure | Default '~/Downloads'
            - _format: str, format to save figure with | Default 'pdf'
        Related to plotting layout:
            - figh: fig height in inches | Default None
            - figratio: float, fig_width=fig_height*n_columns*fig_ratio | Default None
            - transpose: bool, whether to transpose rows/columnP (by defaults, events are rows and units columns) | Default False
        Related to heatmap plotting:
            - as_heatmap: bool, whether to represent data as heatmaps rather than columns of 2D PSTHs | Default True
            - vmin: float, min value of colormap of heatmap | Default None
            - center: float, center value of colormap of heatmap | Default None
            - vmax: float, max value of colormap of heatmap  | Default None
            - cmap_str: str, colormap of heatmap  | Default None
    '''
    ## TODO overlay=False, overlay_dim='events',
    nevents=len(events)
    ntrains=len(trains)
    assert nevents>0 and ntrains>0, "You must provide at least one event and one train!"
    if trains_col_groups is None: trains_col_groups=[0]*ntrains
    ntraingroups=np.unique(trains_col_groups).shape[0]

    if events_col is None:
        colorfamilies = get_color_families(ntraingroups, nevents)
    else:#convert to rgb
        if isinstance(events_col,str): # assumes colormap if str
            colorfamilies = get_color_families(ntraingroups, nevents, events_col)
        elif assert_iterable(events_col):
            if isinstance(events_col[0],str):
                events_col=[to_rgb(c) for c in events_col]
            colorfamilies = [[c]*ntraingroups for c in events_col]
        else:
            raise TypeError('You must provide a LIST of colors or a colormap string.')


    assert ntrains==len(trains_str)==len(trains_col_groups)
    assert nevents==len(events_str)==len(colorfamilies)

    assert len(psthw)==2
    psthw=[psthw[0], psthw[1]+psthb]

    # Plot as 2D grid of PSTHs
    if not as_heatmap:

        (nrows, ncols) = (len(events), len(trains)) if not transpose else (len(trains), len(events))
        if overlap_events: (nrows, ncols) = (1,ncols) if not transpose else (nrows, 1)

        if figh is None: figh=nrows*1.5 # 10 for 7 is good
        if figratio is None: figratio=3
        figw=figh*(ncols/nrows)*figratio
        figsize=(figw,figh)

        # pre-generate figure axes
        fig = plt.figure(figsize=figsize)
        ax_ids=np.arange(nrows*ncols).reshape((nrows,ncols))+1
        axes=ax_ids.copy().astype(object)
        for ei in range(len(events)):
            if overlap_events and (ei != 0): continue
            for ti in range(len(trains)):
                if transpose:
                    ax_id=ax_ids[ti,ei]
                    axes[ti,ei]=fig.add_subplot(nrows, ncols, ax_id)
                else:
                    ax_id=ax_ids[ei,ti]
                    axes[ei,ti]=fig.add_subplot(nrows, ncols, ax_id)

        # plot
        for ei, (e, es, cf) in enumerate(zip(events, events_str, colorfamilies)):
            for ti, (t, ts) in enumerate(zip(trains, trains_str)):
                if overlap_events: ei=0
                ax_id=ax_ids[ei,ti] if not transpose else ax_ids[ti,ei]
                ax_psth=axes[ei,ti] if not transpose else axes[ti,ei]

                legend_label=es if ((ax_id==ax_ids[-1,-1])&(overlap_events)) else None

                xlab='Time (ms)' if ax_id in ax_ids[-1,:] else ''
                ylab='IFR\n(zscore)' if zscore else r'$\Delta$ FR (spk/s)' if bsl_subtract else 'IFR (spk/s)'
                event_str = es if not overlap_events else ''
                (ttl_s, y_s) = (ts, event_str) if not transpose else (event_str, ts)
                ylab= f'{y_s}\n{ylab}' if ax_id in ax_ids[:,0] else ''
                ttl=ttl_s if ax_id in ax_ids[0,:] else None

                tc=cf[trains_col_groups[ti]]

                psth_plot(t, e, psthb, psthw,
                          remove_empty_trials=True, events_toplot=events_toplot, events_color='k',
                           title=ttl, color=tc, legend_label=legend_label, legend=False,
                           saveDir=saveDir, saveFig=False, ret_data=False, _format=_format,
                           zscore=zscore, bsl_subtract=bsl_subtract, bsl_window=bsl_window, ylim=ylim,
                           convolve=convolve, gsd=gsd, xticks=None, xticklabels=None, xlabel=xlab, ylabel=ylab,
                           ax=ax_psth, figsize=None, tight_layout=False, hspace=0.5, wspace=0.5)

        fig.tight_layout()
        if overlap_events: plt.legend()

        if saveFig:save_mpl_fig(fig, title, saveDir, _format)

        return fig

    # Plot as heatmaps
    if figratio is None: figratio=6
    if figh is None: figh = 2.5
    figw=figratio*figh/len(events)
    figsize=(figw,figh)
    fig = plt.figure(figsize=figsize)
    nmaps=len(events) if not transpose else len(trains)
    grid = plt.GridSpec(nmaps, 1, wspace=0.2, hspace=0.3)
    (l1,ls1,l2,ls2)=(events, events_str, trains, trains_str)
    if transpose:(l1,ls1,l2,ls2)=(l2,ls2,l1,ls1)
    for _i1, (_1, _s1) in enumerate(zip(l1,ls1)):
        Y=None
        ax_im=fig.add_subplot(grid[_i1,:])
        for _i2, (_2, _s2) in enumerate(zip(l2,ls2)):
            (e,t)=(_1,_2) if not transpose else (_2,_1)
            x, y, y_p, y_p_var = get_processed_ifr(t, e, b=psthb, window=psthw, remove_empty_trials=True,
                                                      zscore=zscore, zscoretype='within',
                                                      convolve=convolve, gsd=gsd, method='gaussian_causal',
                                                      bsl_subtract=bsl_subtract, bsl_window=bsl_window)
            Y=y_p if Y is None else np.vstack([Y,y_p])
        Y=npa(Y)
        if Y.ndim==1: Y=Y[np.newaxis,:] # handles case where 1 unit
        if vmin is None: vmin1 = 0 if not (zscore|bsl_subtract) else -max(abs(0.9*Y.min()),abs(0.9*Y.max()))
        else: vmin1 = vmin
        if center is None: center1 = 0.4*Y.max() if not (zscore|bsl_subtract) else 0
        else: center1 = center
        if vmax is None: vmax1 = 0.8*Y.max() if not (zscore|bsl_subtract) else max(abs(0.9*Y.min()),abs(0.9*Y.max()))
        else: vmax1 = vmax
        if cmap_str is None: cmap_str = 'viridis' if not (zscore|bsl_subtract) else 'RdBu_r'
        nunits=Y.shape[0]
        y_ticks_labels=trains_str if not transpose else events_str
        clab='Inst. firing rate (spk/s)' if not zscore else 'Inst. firing rate (zscore)'
        ylab=f'Units\n{_s1}' if not transpose else f'Events\n{_s1}'
        tc=colorfamilies[_i1][trains_col_groups[_i2]] if not transpose else colorfamilies[_i2][trains_col_groups[_i1]]
        xlab='Time (ms)' if _i1==len(l1)-1 else None
        imshow_cbar(Y, origin='top', xevents_toplot=events_toplot, events_color=tc,
                    xvalues=np.arange(psthw[0], psthw[1], psthb), yvalues=np.arange(nunits)+1,
                    xticks=None, yticks=np.arange(Y.shape[0])+1,
                    xticklabels=None, yticklabels=y_ticks_labels, xlabel=xlab, xtickrot=0,
                    ylabel=ylab, title=None,
                    cmapstr=cmap_str, vmin=vmin1, vmax=vmax1, center=center1, colorseq='nonlinear',
                    clabel=clab, cticks=None,
                    figsize=figsize, aspect='auto', function='imshow', ax=ax_im, tight_layout=False,
                    cmap_h=0.6/nmaps)

    if title is not None: fig.suptitle(title)
    fig.tight_layout()
    if saveFig:save_mpl_fig(fig, title, saveDir, _format)
    return fig

#%% Correlograms ##############################################################################################

def plt_ccg(uls, CCG, cbin=0.04, cwin=5, bChs=None, fs=30000, saveDir='~/Downloads', saveFig=True,
            _format='pdf', labels=True, title=None, color=None,
            ylim=None, normalize='Hertz', ccg_mn=None, ccg_std=None,
            figsize=None, show_hz=False, style='line', hide_axis=False, show_ttl=True,
            prettify=True, **mplp_kwargs):
    """
    Plots precomputed crosscorrelogram between a pair of units.
    Arguments:
        - uls: list of unit indices
        - CCG: np array, crosscorrelogram (n_bins,) array
        - cbin: float, bin size in ms
        - cwin: float, full window size in ms
        - bChs: list of peak channels for each unit
        - fs: int, sampling frequency (to convert cbincorreclty)

        - saveDir: str, directory to save figure
        - saveFig: bool, whether to save figure
        - _format: str, format to save figure

        - labels: bool, whether to show figure labels and splines
        - title: title of figure
        - color: color of CCG
        - ylim: list of floats, y axis limits
        - normalize: str, normalization method (Hertz, Counts, Pearson or zscore)
        - ccg_mn: np array, mean CCG
        - ccg_std: np array, std CCG
        - figsize: tuple of floats, figure size
        - show_hz: bool, whether to show Hz on a second y axis
        - style: str 'line' or 'bar', style of plot
        - hide_axis: bool, whether to hide axis
        - show_ttl: bool, whether to show title

        - prettify: bool, whether to apply mplp() prettification or not
        - **mplp_kwargs: any additional formatting parameters, passed to mplp()
    """
    global phyColorsDic
    assert style in ['line', 'bar']

    fig, ax = plt.subplots()

    # x axis

    cbin = np.clip(cbin, 1000*1./fs, 1e8)
    x=np.linspace(-cwin*1./2, cwin*1./2, CCG.shape[0])
    assert x.shape==CCG.shape

    # y axis
    y=CCG.copy()
    if ylim is None:
        if normalize in ['Hertz','Counts']:
            yl=max(CCG)
            ylim=[0,int(yl)+5-(yl%5)]
        elif normalize=='Pearson':
            yl=max(CCG)
            ylim=[0, yl+0.01-(yl%0.01)]
        else:
            yl=np.max(np.abs(CCG))
            ylim=[-yl, yl]

    # pick color and plot
    if isinstance(color, int): # else, an actual color is passed
        color=phyColorsDic[color]
    elif color is None:
        color='black'

    # plotting
    if style=='bar':
        #ax.step(x, y, color='black', alpha=1, where='mid', lw=1)
        ax.bar(x=x, height=y+ abs(ylim[0]), width=cbin/2, color=color, edgecolor=color, bottom=ylim[0]) # Potentially: set bottom=0 for zscore
    elif style=='line':
        ax.plot(x, y, color='black', alpha=1)
        if normalize in ['Hertz','Pearson','Counts']:
            ax.fill_between(x, x*0, y, color=color)
        else:
            ax.fill_between(x, ylim[0]*np.ones(len(x)), y, color=color)

    # plot formatting
    ax.plot([0,0], ylim, c=[0.7, 0.7, 0.7], lw=1, zorder=-1)
    
    if normalize not in ['Hertz','Counts', 'Pearson']:
            ax.plot([x[0], x[-1]], [0,0], c=[0.7, 0.7, 0.7], lw=1, zorder=-1)
    if not isinstance(title, str) and show_ttl:
        if bChs is None:
            title=f"{uls[0]}->{uls[1]}"
        else:
            title=f"{uls[0]}@{bChs[0]}->{uls[1]}@{bChs[1]}"
    
    ylabdic={'Counts':'Counts',
                'Hertz':'spk/s',
                'Pearson':'Pearson',
                'zscore':'z-score'}
    if labels:
        ylabel=f"Crosscorr. ({ylabdic[normalize]})" if normalize in ylabdic else f"{normalize}"
    else:
        ylabel=None

    if figsize is None: figsize = (4.5, 4)
    mplp(fig, ax, figsize=figsize,
         title=title,
         xlabel='Time (ms)', ylabel=ylabel,
         title_s=20, axlab_s=20, ticklab_s=20, axlab_w = 'regular',
         xlim=[-cwin*1./2, cwin*1./2], ylim=ylim, hide_axis=hide_axis,
         prettify=prettify, **mplp_kwargs)

    # optional second y axis
    if ccg_mn is not None and ccg_std is not None and show_hz:
        ax2 = ax.twinx()
        ax2.set_ylabel('Crosscorr. (spk/s)', fontsize=18, rotation=270, va='bottom')
        ax2ticks=[np.round(ccg_mn+tick*ccg_std,1) for tick in ax.get_yticks()]
        ax2.set_yticks(ax.get_yticks())
        ax2.set_yticklabels(ax2ticks, fontsize=16)
        ax2.set_ylim(ylim)
        [ax2.spines[sp].set_visible(False) for sp in ['top']]


    # Eventually save figure
    if saveFig:
        save_mpl_fig(fig, 'ccg{0}-{1}_{2}_{3:.2f}'.format(uls[0], uls[1], cwin, cbin), saveDir, _format)

    return fig

def plt_acg(unit, ACG, cbin=0.2, cwin=80, bChs=None, color=0, fs=30000,
            saveDir='~/Downloads', saveFig=False, _format='pdf',
            labels=True, title=None, ref_per=True, ax=None,
            ylim1=0, ylim2=0, normalize='Hertz', acg_mn=None, acg_std=None, figsize=None,
            hide_axis=False, prettify=True, **mplp_kwargs):
    """
    Plots precomputed autocorrelogram.
    Arguments:
        - unit: unit index
        - ACG: np array, crosscorrelogram (n_bins,) array
        - cbin: float, bin size in ms
        - cwin: float, full window size in ms
        - bChs: peak channels of unit

        - color: color of ACG
        - fs: int, sampling frequency (to convert cbincorreclty)

        - saveDir: str, directory to save figure
        - saveFig: bool, whether to save figure
        - _format: str, format to save figure

        - labels: bool, whether to show figure labels and splines
        - title: title of figure
        - ref_per: bool, whether to plot refractory period (+/- 1ms)
        - ax: matplotlib axis, axis to plot on (if None, creates new figure)
        - ylim1: float, lower y axis limit
        - ylim2: float, upper y axis limit
        - normalize: str, normalization method (Hertz, Counts, Pearson or zscore)
        - acg_mn: float, mean of ACG if was normalized
        - acg_std: np array, std of ACG if was normalized

        - figsize: tuple of floats (x, y), figure size in inches
        - hide_axis: bool, whether to hide axis

        - prettify: bool, whether to apply mplp() prettification or not
        - **mplp_kwargs: any additional formatting parameters, passed to mplp()
    """
    global phyColorsDic
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    # x axis
    cbin = np.clip(cbin, 1000*1./fs, 1e8)
    x=np.linspace(-cwin*1./2, cwin*1./2, ACG.shape[0])
    assert x.shape==ACG.shape

    # y axis
    if ylim1==0 and ylim2==0:
        if normalize in ['Hertz','Counts']:
            ylim1=0
            yl=max(ACG); ylim2=int(yl)+5-(yl%5);
        elif normalize=='Pearson':
            ylim1=0
            yl=max(ACG); ylim2=yl+0.01-(yl%0.01);
        elif normalize=='zscore':
            yl1=min(ACG);yl2=max(ACG)
            ylim1=yl1-0.5+(abs(yl1)%0.5);ylim2=yl2+0.5-(yl2%0.5)
            ylim1, ylim2 = min(-3, ylim1), max(3, ylim2)
            ylim1, ylim2 = -max(abs(ylim1), abs(ylim2)), max(abs(ylim1), abs(ylim2))

    if normalize in ['Hertz', 'Pearson', 'Counts']:
        y=ACG.copy()
    elif normalize=='zscore':
        y=ACG.copy()+abs(ylim1)

    # optional secondary y axis
    if acg_mn is not None and acg_std is not None:
        ax2 = ax.twinx()
        ax2.set_ylabel('Autocorrelation (spk/s)', fontsize=16, rotation=270, va='bottom')
        ax2ticks=[np.round(acg_mn+tick*acg_std,1) for tick in ax.get_yticks()]
        ax2.set_yticks(ax.get_yticks())
        ax2.set_yticklabels(ax2ticks, fontsize=16)
        ax2.set_ylim([ylim1, ylim2])

    # pick color and plot
    if isinstance(color, int): # else, an actual color is passed
        color=phyColorsDic[color]
    ax.fill_between(x, y*0, y, color=color, step='mid')
    ax.step(x, y, where='mid', color='black', lw=1)

    # Plot formatting
    if labels:
        if not isinstance(title, str):
            if  bChs is None:
                title=f"{unit}"
            else:
                assert len(bChs)==1
                title=f"{unit}@{bChs[0]}"
        if ref_per:
            ax.plot([-1, -1], [ylim1, ylim2], color='black', linestyle='--', linewidth=1)
            ax.plot([1, 1], [ylim1, ylim2], color='black', linestyle='--', linewidth=1)

    ylabdic={'Counts':'Counts',
                    'Hertz':'spk/s',
                    'Pearson':'Pearson',
                    'zscore':'z-score'}
    ylabel=f"Autocorrelation ({ylabdic[normalize]})" if labels else None

    if figsize is None: figsize = (4.5,4)
    mplp(fig, figsize=figsize,
    title=title, xlabel='Time (ms)', ylabel=ylabel,
    title_s=20, axlab_s=20, ticklab_s=20,
    xlim=[-cwin*1./2, cwin*1./2], ylim=[ylim1, ylim2],
    hide_axis=hide_axis, prettify=prettify, **mplp_kwargs)

    # Eventually save figure
    if saveFig:
        save_mpl_fig(fig, 'acg{}-{}_{:.2f}'.format(unit, cwin, cbin), saveDir, _format)

    return fig


def plt_ccg_subplots(units, CCGs, cbin=0.2, cwin=80, bChs=None, saveDir='~/Downloads',
                     saveFig=False, _format='pdf', figsize=None,
                     labels=True, show_ttl=True, title=None,
                     ylim_acg=None, ylim_ccg=None, share_y=0, normalize='zscore',
                     acg_color=None, ccg_color='black', hide_axis=False, pad=0,
                     prettify=True, style='line',
                     show_hz=False, ccg_means=None, ccg_deviations=None,
                     **mplp_kwargs):

    ## format parameters
    if acg_color is not None and not isinstance(acg_color, str) and not isinstance(acg_color, int):
        assert len(acg_color) == CCGs.shape[0],\
            ("If acg_color is not a string, it must be a list of colors "
            "with the same length as the number of units (e.g. [[r,g,b]] for 1 unit.")

    ## Instanciate figure and format x axis/channels
    l=CCGs.shape[0]
    if figsize is None: figsize=(4.5*l/2,4*l/2)
    if show_hz: figsize = (figsize[0]*1.2, figsize[1])
    fig = plt.figure(figsize=figsize)

    x=np.round(np.linspace(-cwin/2, cwin/2, CCGs.shape[2]),1)
    if bChs is not None:
        bChs=npa(bChs).astype(np.int64)

    ## precompute y limits (in case of y_sharing)
    ylims=[]
    acg_mask = npa([]).astype(bool)
    for row in range(l):
        for col in range(l):
            if normalize!='mixte':normalize1=normalize
            if row>col: continue
            ylim=None
            on_acg = (row==col)
            if on_acg:
                acg_mask=np.append(acg_mask,[True])
                y=CCGs[row,col,:]
                if normalize=='mixte': normalize1='Hertz'
                if ylim_acg is not None: ylim=ylim_acg
            else:
                acg_mask=np.append(acg_mask,[False])
                if normalize=='mixte':
                    y=zscore(CCGs[row,col,:], 4./5)
                    normalize1='zscore'
                else:
                    y=CCGs[row,col,:]
                if ylim_ccg is not None: ylim=ylim_ccg

            if ylim is None:
                margin = abs(np.max(y)-np.min(y))*0.01
                ylim = [np.min(y)-margin, np.max(y)+margin]
            if normalize1 in ['Hertz','Pearson','Counts']:
                ylims.append([0, ylim[1]])
            elif normalize1=='zscore':
                ylmax=max(np.abs(ylim))
                ylims.append([-ylmax, ylmax])
            else:
                ylims.append(ylim)

    ylims=npa(ylims)
    if share_y:
        if normalize=='mixte':
            ylims_ccg = ylims[~acg_mask]
            ylims_acg = ylims[acg_mask]
            yl_max_ccg = np.max(ylims_ccg[:,1])
            yl_max_acg = np.max(ylims_acg[:,1])
            ylims[acg_mask,1] = yl_max_acg
            ylims[~acg_mask,0] = -yl_max_ccg
            ylims[~acg_mask,1] = yl_max_ccg
        else:
            yl_max = np.max(ylims[:,1])
            if normalize in ['Hertz','Pearson']:
                ylims[~acg_mask,0] = -yl_max
                ylims[~acg_mask,1] = yl_max
            else:
                ylims[acg_mask,1] = yl_max

    ## Actually generate subplots, plot and frame
    pbar = tqdm(total=(l**2-l)//2+l, desc="Plotting CCGs")
    i=0
    for row in range(l):
        for col in range(l):
            # create subplot
            ax=fig.add_subplot(l, l, 1+row*l+col%l)
            if row>col:
                mplp(ax=ax, hide_axis=True)
                continue

            # Process y data and pick color
            if normalize!='mixte':normalize1=normalize
            on_acg = (row==col)
            if on_acg:
                acg_mask=np.append(acg_mask,[True])
                if acg_color is None:
                    color = phyColorsDic[row%6]
                else:
                    if isinstance(acg_color, str):
                        color = acg_color
                    else:
                        color = acg_color[row]
                y=CCGs[row,col,:]
                if normalize=='mixte': normalize1='Hertz'
            else:
                acg_mask=np.append(acg_mask,[False])
                color=ccg_color
                if normalize=='mixte':
                    y=zscore(CCGs[row,col,:], 4./5)
                    normalize1='zscore'
                else:
                    y=CCGs[row,col,:]

            # plot content
            if style=='line':
                ax.plot(x, y, color=color, alpha=0)
                if normalize1 in ['Hertz','Pearson','Counts']:
                    ax.fill_between(x, x*0, y, color=color)
                else:
                    ax.fill_between(x, ylims[i][0]*np.ones(len(x)), y, color=color)

            elif style=='bar':
                if row == col: ax.step(x, y, color='black', alpha=1, where='mid', lw=1)
                ax.bar(x=x, height=y+abs(ylims[i][0]), width=cbin, color=color, bottom=ylims[i][0])
            if row != col: ax.plot([0,0], ylims[i], c=[0.7, 0.7, 0.7], lw=1, zorder=10)

            # plot framing
            norm_str={'mixte':'', 'zscore':'(zscore)', 'Hertz':'(spk/s)',
                      'Pearson':'(Pearson)','Counts':'(Counts)'}

            if row==col:
                ylabel = f"Crosscorr. {norm_str[normalize]}" if normalize in norm_str else f"{normalize}"
            else:
                ylabel = None
            xlabel = 'Time (ms)' if row==col else None
            if labels:
                if bChs is not None:
                    ttl=f"{units[row]}@{bChs[row]}>{units[col]}@{bChs[col]}" if any(bChs) else f"{units[row]}>{units[col]}"
                else:
                    ttl = f"{units[row]}>{units[col]}"
            else:
                ttl = None
            if not show_ttl: ttl=None

            if show_hz and (not on_acg) and normalize1 == 'zscore' and \
                (ccg_means is not None) and (ccg_deviations is not None):
                ccg_mn = ccg_means[row,col]
                ccg_std = ccg_deviations[row,col]
                ax2 = ax.twinx()
                ax2ticks=[np.round(ccg_mn+tick*ccg_std,1) for tick in ax.get_yticks()]
                ax2.set_yticks(ax.get_yticks())
                ax2.set_yticklabels(ax2ticks, fontsize=18)
                ax2.set_ylim(ylims[i])
                [ax2.spines[sp].set_visible(False) for sp in ['top']]

            mplp(ax=ax, figsize=figsize, ylim=ylims[i], xlim=[-cwin*1./2, cwin*1./2],
                lw=1, title=ttl, ylabel=ylabel, xlabel=xlabel,
                title_s=8, title_w='regular',
                axlab_s=16, axlab_w='regular',
                ticklab_s=18, ticklab_w='regular',
                tight_layout=False, hide_axis=hide_axis,
                prettify=prettify, **mplp_kwargs)

            i+=1
            pbar.update(1)

    if title is not None:
        fig.suptitle(title, size=20, weight='bold')
    fig.tight_layout(rect=[0, 0.03, 1, 0.95], pad=pad)
    if saveFig:
        save_mpl_fig(fig, f"ccg_{title}_{str(units).replace(' ', '')}-{cwin}_{cbin}", saveDir, _format)

    return fig


def plot_acg(dp, unit, cbin=0.2, cwin=80, normalize='Hertz', periods='all',
             saveDir='~/Downloads', saveFig=False, _format='pdf', figsize=None, verbose=False,
             color=0, labels=True, title=None, ref_per=True, ylim=[0, 0], ax=None,
             acg_mn=None, acg_std=None, again=False,
             train=None, hide_axis=False, prettify=True, enforced_rp=0, **mplp_kwargs):
    """
    Plots precomputed autocorrelogram.
    Arguments:
        - dp: str, data path
        - unit: float, unit index
        - cbin: float, binsize (ms)
        - cwin: float, full window size (ms)
        - normalize: str in ['Counts', 'Hertz', 'Pearson', 'zscore', 'mixte'], unit of y axis
        - periods: 'all' or [(t1,t2), (t3,t4)...], periods to use to compute CCG (in SECONDS)

        - saveDir: str, save directory for figure
        - saveFig: bool, whether to dave Figure at saveDir
        - _format: str, format to save fig (pdf, svg, eps, png, jpeg...)
        - figsize: (x,y) tuple, size of figure in inches
        - verbose: bool, if True prints information

        - color: string, self explanatory (can also use 0-5 as keys of npyx.utils.phyColorsDic)
        - labels: bool, whether to plot axis labels/title
        - title: str, figure title
        - ref_per: bool, if True plot vertical lines highlighting 2ms refractory period

        - ylim: [float, float], ylim for autocorrelograms in case as_grid is True
        - ax: matplotlib axis, axis to plot on (if None, creates new figure)
        - acg_mn: float, optionally feed externally calculated mean to zscore the CCG
        - acg_std: float, optionally feed externally calculated std to zscore the CCG

        - again: bool, whether to recompute the CCG
        - train: np array (n_spikes,), optional externally fed train to compute ACG (in samples, not seconds).
                 If used, use any integers as 'units'.

        - hide_axis: bool, whether to hide axis
        - prettify: bool, whether to apply mplp() prettification or not
        - **mplp_kwargs: any additional formatting parameters, passed to mplp()

    Returns:
        - fig: matplotlib figure object
    """
    saveDir = op.expanduser(saveDir)
    if train is not None:
        bChs = None
    else:
        bChs = get_depthSort_peakChans(dp, units=[unit])[:, 1].flatten()
    ylim1, ylim2 = ylim[0], ylim[1]

    ACG = acg(dp, unit, cbin, cwin, fs=30000, normalize=normalize,
              verbose=verbose, periods=periods, again=again, train=train, enforced_rp=enforced_rp)
    if normalize == 'zscore':
        ACG_hertz = acg(dp, unit, cbin, cwin, fs=30000, normalize='Hertz', verbose=verbose, periods=periods)
        acg25, acg35 = ACG_hertz[:int(len(ACG_hertz) * 2. / 5)], ACG_hertz[int(len(ACG_hertz) * 3. / 5):]
        acg_std = np.std(np.append(acg25, acg35))
        acg_mn = np.mean(np.append(acg25, acg35))
    fig = plt_acg(unit, ACG, cbin, cwin, bChs, color, 30000, saveDir, saveFig, _format=_format,
                  labels=labels, title=title, ref_per=ref_per, ylim1=ylim1, ylim2=ylim2, ax=ax,
                  normalize=normalize, acg_mn=acg_mn, acg_std=acg_std, figsize=figsize, hide_axis=hide_axis,
                  prettify=prettify, **mplp_kwargs)

    return fig


def plot_ccg(dp, units, cbin=0.2, cwin=80, normalize='mixte',
             saveDir='~/Downloads', saveFig=False, _format='pdf', figsize=None, periods='all',
             labels=True, title=None, show_ttl=True, color=None, CCG=None,
             ylim_acg=None, ylim_ccg=None, share_y=False,
             ccg_means=None, ccg_deviations=None, again=False, trains=None, as_grid=False, show_hz=False,
             use_template=True, enforced_rp=0, style='line', hide_axis=False, pad=0,
             prettify=True, **mplp_kwargs):
    """
    Arguments:
        - dp: str, data path
        - units: [float, float], list of 2 unit indices
        - cbin: float, binsize (ms)
        - cwin: float, full window size (ms)
        - normalize: str in ['Counts', 'Hertz', 'Pearson', 'zscore', 'mixte'], unit of y axis

        - saveDir: str, save directory for figure
        - saveFig: bool, whether to dave Figure at saveDir
        - _format: str, format to save fig (pdf, svg, eps, png, jpeg...)
        - figsize: (x,y) tuple, size of figure in inches

        - periods: 'all' or [(t1,t2), (t3,t4)...], periods to use to compute CCG (in SECONDS)

        - labels: bool, whether to plot axis labels/title
        - title: str, figure title
        - show_ttl: bool, whether to show title
        - color: int, classical phy ACG colors (-1 black, 0 blue, 1 red...

        - CCG: array, optionnaly feed externally computed CCG

        - ylim_acg: [float, float], ylim for autocorrelograms in case as_grid is True
        - ylim_ccg: [float, float], ylim for crosscorrelogram(s)
        - share_y: bool, whether to use the same y limit for all CCGs if as_grid is True

        - ccg_means: (len(units), len(units),) array, optionally feed externally calculated mean(s) to zscore the CCG(s)
        - ccg_deviations: (len(units), len(units),) array, optionally feed externally calculated std(s) to zscore the CCG(s)

        - again: bool, whether to recompute the CCG
        - trains: [array1, array2...], optional externally fed list of trains to compute ACGs/CCGs (in samples). Then use any integers as 'units'.
        - as_grid: bool, also plot units autocorrelograms along the diagonal (only relevant when plotting 2 units)
        - show_hz: bool, whether to add a second y axis and show the values corresponding to z-score units in Hz (only applies if normalize='zscore' or 'mixte')

        - use_template: bool, whether to use the template files to find the peak channel
        - enforced_rp: float, enforced refractory period (will remove spikes happening within enforced_rp ms of another) | Default 0
        - style: str, 'line' or 'bar' (to plot ccg as a line or a histogram)
        - hide_axis: bool, whether to hide axis
        - pad: float, padding between subplots (in inches)

        - prettify: bool, whether to apply mplp() prettification or not
        - **mplp_kwargs: any additional formatting parameters, passed to mplp()

    Returns:
        - fig: matplotlib figure object
    """
    assert assert_iterable(units)
    units=list(units)
    _, _idx=np.unique(units, return_index=True)
    units=npa(units)[np.sort(_idx)].tolist()
    assert normalize in ['Counts', 'Hertz', 'Pearson', 'zscore', 'mixte'], "WARNING ccg() 'normalize' argument should be a string in ['Counts', 'Hertz', 'Pearson', 'zscore', 'mixte']."#
    if normalize=='mixte' and len(units)==2 and not as_grid: normalize='zscore'
    saveDir=op.expanduser(saveDir)

    if trains is None:
        bChs = get_depthSort_peakChans(dp, units=units, use_template=use_template)[:,1].flatten()
    else:
        bChs = None

    if CCG is None:
        normalize1 = normalize if normalize!='mixte' else 'Hertz'
        CCG = ccg(dp, units, cbin, cwin, fs=30000, normalize=normalize1, verbose=0, periods=periods, again=again, trains=trains, enforced_rp=enforced_rp)
    assert CCG is not None

    if normalize in ['mixte', 'zscore']:
        CCG_hertz=ccg(dp, units, cbin, cwin, fs=30000, normalize='Hertz', verbose=0,
                        periods=periods, again=again, trains=trains)
        nbins = CCG_hertz.shape[2]
        ccg25, ccg35 = CCG_hertz[:,:,:int(nbins*2./5)], CCG_hertz[:,:,int(nbins*3./5):]
        ccg_baseline = np.concatenate((ccg25, ccg35), axis=2)
        ccg_deviations = np.std(ccg_baseline, axis=2)
        ccg_means = np.mean(ccg_baseline, axis=2)

    if CCG.shape[0]==2 and not as_grid:
        if ccg_means is not None: ccg_means = ccg_means[0,1]
        if ccg_deviations is not None: ccg_deviations = ccg_deviations[0,1]
        fig = plt_ccg(units, CCG[0,1,:], cbin, cwin, bChs, 30000, saveDir, saveFig, _format,
                      labels=labels, title=title, color=color, ylim=ylim_ccg,
                      normalize=normalize, ccg_mn=ccg_means, ccg_std=ccg_deviations,
                      figsize=figsize, style=style, hide_axis=hide_axis, show_hz=show_hz, show_ttl=show_ttl,
                      prettify=prettify, **mplp_kwargs)
    else:
        fig = plt_ccg_subplots(units, CCG, cbin, cwin, bChs, saveDir, saveFig, _format, figsize,
                               labels=labels, show_ttl=show_ttl,title=title,
                               ylim_acg=ylim_acg, ylim_ccg=ylim_ccg, share_y=share_y, normalize=normalize,
                               acg_color=color, hide_axis=hide_axis, pad=pad, prettify=prettify, style=style,
                               show_hz=show_hz, ccg_means=ccg_means, ccg_deviations=ccg_deviations, **mplp_kwargs)

    return fig

def plot_scaled_acg( dp, units, cut_at = 150, bs = 0.5, min_sec = 180, again = False):
    """
    Make the plot used for showing different ACG shapes
    Return: plot
    """
    # check if units are a list
    if isinstance(units, (int, np.int16, np.int32, np.int64)):
        # check if it's len 1
        units = [units]
    elif isinstance(units, str):
        if units.strip() == 'all':
            units = get_units(dp, quality = 'good')
        else:
            raise ValueError("You can only pass 'all' as a string")
    elif isinstance(units, list):
        pass
    else:
            raise TypeError("Only the string 'all', ints, list of ints or ints disguised as floats allowed")

    rec_name = str(dp).split('/')[-1]

    normed_new, isi_mode, isi_hist_counts, isi_hist_range, acg_unnormed  = scaled_acg(dp, units, cut_at = cut_at, bs = bs, min_sec = min_sec, again = again)

    # find the units where the normed_new values pass our filter
    good_ones = np.sum(normed_new, axis = 1) !=0
    good_acgs = normed_new[good_ones]
    good_units = np.array(units)[good_ones]
    good_isi_mode = isi_mode[good_ones]
    good_isi_hist_counts = isi_hist_counts[good_ones]
    good_isi_hist_range = isi_hist_range[good_ones]
    good_acg_unnormed = acg_unnormed[good_ones]

    for unit_id in range(good_units.shape[0]):
        unit = good_units[unit_id]
        fig,ax = plt.subplots(3)
        fig.suptitle(f"Unit {unit} on dp \n {rec_name} \n and mfr mean_fr and isi_hist_mode isi_hist_mode len acg.shape[0]")
        ax[0].vlines(good_isi_mode[unit_id], 0, np.nanmax(good_isi_hist_counts[unit_id]), color = 'red')
        ax[0].bar(good_isi_hist_range[unit_id],good_isi_hist_counts[unit_id])
        ax[1].vlines(good_isi_mode[unit_id], 0,np.nanmax(good_acg_unnormed[unit_id]), color = 'red')
        ax[1].plot(np.arange(0, good_acg_unnormed[unit_id].shape[0]*bs, bs),good_acg_unnormed[unit_id])
#                    ax[2].plot(smooth_new)
        ax[2].plot(good_acgs[unit_id])
#                    ax[2].plot(unit_normed)
        ax[2].vlines(100, 0,np.max(good_acgs[unit_id]), color = 'red')
        fig.tight_layout()

def plot_3d_acg(dp, u, cbin, cwin, normalize='Hertz',
                num_firing_rate_bins=10, smooth_sd=250,
                periods='all',
                n_log_bins=None, start_log_ms=1, smooth_sd_log=1,
                train=None, enforced_rp=0, again=False, plot_1D=False):

    acg3d, t, f = acg_3D(dp, u, cbin, cwin, normalize=normalize,
            verbose=False, periods=periods, again=again,
            train=train, enforced_rp=enforced_rp,
            num_firing_rate_bins=num_firing_rate_bins, smooth=smooth_sd)
        
    return plt_3d_acg(acg3d, t, f, cbin, cwin,
                n_log_bins=n_log_bins, start_log_ms=start_log_ms,
                smooth_sd_log=smooth_sd_log, plot_1D=plot_1D)

def plt_3d_acg(acg3d, t, f, cbin, cwin,
                n_log_bins=None, start_log_ms=1, smooth_sd_log=1,
                plot_1D=False):

    if n_log_bins is None:
        fig = imshow_cbar(acg3d, xvalues=t,
                    yticks=np.arange(len(f)), yvalues=np.arange(len(f)), 
                    yticklabels=np.round(f).astype(int),
                    origin='bottom', cmapstr='viridis', vmin=0,
                    xtickrot=0,
                    xlabel="Time (ms)", ylabel="Rate (sp/s)", clabel="Autocorr. (sp/s)")

    else:
        assert n_log_bins > 1
        log_acg, t_log = convert_acg_log(acg3d, cbin, cwin,
                                     n_log_bins=n_log_bins, start_log_ms=start_log_ms,
                                     smooth_sd=smooth_sd_log, plot=plot_1D)

        log_ticks = [10,1000]
        log_ticks = np.concatenate((-log_ticks[::-1], [0], log_ticks))
        plt.xscale('symlog')
        fig = imshow_cbar(log_acg,
                        function = 'pcolor',
                        xvalues = t_log, 
                        xticks = log_ticks, xticklabels=log_ticks,
                        yticks=np.arange(len(f)), yvalues=np.arange(len(f)),
                        yticklabels=np.round(f).astype(int),
                        origin='bottom', cmapstr='viridis', vmin=0,
                        xtickrot=0,
                        xlabel="Time (ms)", ylabel="Rate (sp/s)", clabel="Autocorr. (sp/s)")
        
    return fig

#%% Heatmaps including correlation matrices ##############################################################################################

def imshow_cbar(im, origin='top', xevents_toplot=[], yevents_toplot=[], events_color='k', events_lw=2,
                xvalues=None, yvalues=None, xticks=None, yticks=None,
                xticklabels=None, yticklabels=None, xlabel=None, ylabel=None, xtickrot=45, title='',
                cmapstr="RdBu_r", vmin=None, vmax=None, center=None, colorseq='nonlinear',
                clabel='', cticks=None,
                figsize=(6,4), aspect='auto', function='imshow',
                ax=None, tight_layout=True, cmap_w=0.02, cmap_h=0.5, cmap_pad=0.01,
                prettify=True, show_values=False, saveDir=None, saveFig=False, _format='pdf',
                **kwargs):
    '''
    Essentially plt.imshow(im, cmap=cmapstr), but with a nicer and actually customizable colorbar.

    Arguments:
        - im: 2D array def to matplotlib.pyplot.imshow
        - origin: y axis origin, either top or bottom | Default: top

        - xevents_toplot: list of events to plot as vertical dashed lines
        - yevents_toplot: list of events to plot as horizontal dashed lines
        - events_color: color of the dashed lines
        - events_lw: linewidth of the dashed lines

        - xvalues, yvalues: lists/arrays of lengths im.shape[1] and im.shape[0], respectively.
                            Allows to alter the value to which pixel positions are mapped (which are dumb pixel ranks by default).
        - xticks, yticks: lists/array, allows to alter the position of the ticks (in [0,npixels] space by default, in xvalues/yvalues space if they are provided)
        - xticklabels, yticklabels: list of str, allows to alter the label of the ticks - should have the same size as xticks/yticks
        - xlabel, ylabel: str, labels for the x and y axes

        - xtickrot: int, rotation of the xticklabels (degrees)
        - title: str, figure title

        - cmapstr: string, colormap name from matplotlib ('RdBu_r') or Fabio Crameri package ('batlow')
        - vmin: value to which the lower boundary of the colormap corresponds
        - vmax: value to which the upper boundary of the colormap corresponds
        - center: value to which the center of the colormap corresponds
        - colorseq: string, {'linear', 'nonlinear'}, whether to shrink or not the colormap between the center and the closest boundary
                    when 'center' is not None and isn't equidistant between vmax and vmin
        - clabel: string, colormap label
        - cticks: list of ticks to show

        - figsize: (x,y) tuple, size of figure in inches
        - aspect: {'equal', 'auto'}, see matplotlib.pyplot.imshow documentation
        - function: {'imshow', 'pcolormesh'}, whether to use imshow or pcolormesh to plot the image
        - ax: matplotlib axis, if None, a new figure is created
        - tight_layout: bool, whether to use plt.tight_layout() or not
        - cmap_w: float, width of the colorbar in axes fraction
        - cmap_h: float, height of the colorbar in axes fraction
        - cmap_pad: cmap padding in axes fraction

        - prettify: bool, whether to apply mplp() prettification or not
        - show_values: bool, whether to overlay the values of the pixels or not
        - **kwargs: additional arguments to be passed to the plotting function imshow or pcolormesh (e.g. interpolation='nearest')
    '''
    assert colorseq in ['linear', 'nonlinear']
    if im.ndim==1:
        print('Single row of pixels detected - plotting it horizontally.')
        im=im[np.newaxis,:]
    assert im.ndim==2
    assert isinstance(cmapstr,str), 'cmap must be a string!'

    minimum=im.min() if vmin is None else vmin
    maximum=im.max() if vmax is None else vmax
    if minimum==maximum: maximum = minimum + 1
    rng=maximum-minimum
    if vmin is None: vmin = minimum+0.1*rng if center is None else min(minimum+0.1*rng,center-0.01*rng)
    if vmax is None: vmax = maximum-0.1*rng if center is None else max(maximum-0.1*rng, center+0.01*rng)
    if center is None: center=vmin+((vmax-vmin)/2)
    if cticks is not None: assert cticks[-1]<=vmax and cticks[0]>=vmin

    # Make custom colormap.
    # If center if provided, reindex colors accordingly
    if center is None:
        cmap = get_cmap(cmapstr)
    else:
        cmap = get_bounded_cmap(cmapstr, vmin, center, vmax, colorseq)

    # Define pixel coordinates (default is 0 to n_rows-1 for y and n_columns=1 for x)
    if xvalues is None: xvalues=np.arange(im.shape[1])
    assert len(xvalues)==im.shape[1],\
        f'xvalues should contain {im.shape[1]} values but contains {len(xvalues)}!'
    dx = (xvalues[1]-xvalues[0])/2 if len(xvalues)>1 else xvalues[0]
    if yvalues is None: yvalues=np.arange(im.shape[0])
    assert len(yvalues)==im.shape[0],\
        f'yvalues should contain {im.shape[0]} values but contains {len(yvalues)}!'
    dy = (yvalues[1]-yvalues[0])/2 if len(yvalues)>1 else yvalues[0]
    extent = [xvalues[0]-dx, xvalues[-1]+dx, yvalues[-1]+dy, yvalues[0]-dy]

    # Plot image with custom colormap
    fig, ax = plt.subplots(figsize=figsize) if ax is None else (ax.get_figure(), ax)
    if function=='imshow':
        axim = ax.imshow(im, cmap=cmap, vmin=vmin, vmax=vmax, aspect=aspect,
                         origin={'top':'upper', 'bottom':'lower'}[origin],
                         extent=extent, interpolation='nearest',
                         **kwargs)
    elif function=='pcolor':
        pmeshy = yvalues[::-1] if origin=='top' else yvalues
        axim = ax.pcolormesh(xvalues, pmeshy, im,
                             cmap=cmap, vmin=vmin, vmax=vmax, **kwargs)
    if show_values:
        min_edge = np.min([ax.get_position().width  / im.shape[0],
                           ax.get_position().height / im.shape[1]])
        fontsize = (0.8*min_edge)/0.01 # roughly inch to pt
        colors = axim.cmap(axim.norm(im.ravel()))[:,:-1]
        colors = mpl.colors.rgb_to_hsv(colors).reshape(im.shape + (3,))
        for (j,i),label in np.ndenumerate(im):
            if origin == 'bottom':
                i = im.shape[0]-1-i
            c = 'white' if colors[j, i,-1] < 0.5 else 'black'
            ax.text(i, j, label, fontsize=fontsize,
                    color=c, ha='center', va='center')
            ax.text(i, j, label, fontsize=fontsize,
                    color=c, ha='center', va='center')

    if any(xevents_toplot):
        for e in xevents_toplot:
            yl=ax.get_ylim()
            ax.plot([e,e],yl,lw=events_lw,ls='--',c=events_color)
            ax.set_ylim(yl)
    if any(yevents_toplot):
        for e in yevents_toplot:
            xl=ax.get_xlim()
            ax.plot(xl,[e,e],lw=events_lw,ls='--',c=events_color)
            ax.set_xlim(xl)

    if xticks is None:
        xticks = get_bestticks_from_array(xvalues, light=1)
    if yticks is None:
        yticks = get_bestticks_from_array(yvalues, light=1)
    mplp(fig, ax, figsize=figsize,
          xlim=None, ylim=None, xlabel=xlabel, ylabel=ylabel,
          xticks=xticks, yticks=yticks, xtickslabels=xticklabels, ytickslabels=yticklabels,
          reset_xticks=False, reset_yticks=False, xtickrot=xtickrot, ytickrot=0,
          xtickha={0:'center',45:'right'}[xtickrot], xtickva='top', ytickha='right', ytickva='center',
          axlab_w='regular', axlab_s=20,
          ticklab_w='regular', ticklab_s=16, ticks_direction='out', lw=1,
          title=title, title_w='regular', title_s=12,
          hide_top_right=False, hide_axis=False, tight_layout=False,
          prettify=prettify)

    if tight_layout: fig.tight_layout(rect=[0,0,0.8,1])

    # Add colorbar, nicely formatted
    fig = add_colorbar(fig, ax, axim, vmin, vmax,
                        cmap_w, cmap_h, cticks, clabel, 'regular', pad=cmap_pad)

    if saveFig:
        save_mpl_fig(fig, 'heatmap', saveDir, _format, dpi=500)

    return fig

def add_colorbar(fig, ax, mappable=None, vmin=None, vmax=None,
                 width=0.01, height=0.5, cticks=None,
                 clabel=None, clabel_w='regular', clabel_s=20, cticks_s=16, ctickslabels=None,
                 cmap=None, pad = 0.01, clim=None):
    """
    Add colorbar to figure with a predefined axis.
    
    Makes sure that the size of the predefined axis does not change, but that the figure extends.
    """

    # format vmin and vmax
    if vmin is not None or vmax is not None:
        assert vmin is not None and vmax is not None, "You must provide both vmin and vmax!" 
    if vmin is not None and vmax is not None:
        assert vmin < vmax, "Make sure that vmin < vmax (cannot make a 0-range colorbar...)."
        if cticks is None:
            cticks=get_bestticks(vmin, vmax, light=True)

    # define mappable
    if mappable is None:
        assert vmin is not None or vmax is not None,\
            "If you do not provide a mappable (e.g. ax.collections[0]), you must provide vmin and vmax!"
        assert cmap is not None,\
            "If you do not provide a mappable (e.g. ax.collections[0]), you must provide a colormap (e.g. 'viridis')!"
        norm     = plt.Normalize(vmin, vmax)
        mappable = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        mappable.set_array([])

    # create colorbar axis
    axpos   = ax.get_position()
    cbar_ax = fig.add_axes([axpos.x1+pad*axpos.width, axpos.y0,
                            width*axpos.width, height*axpos.height])

    # add colorbar
    fig.colorbar(mappable, cax=cbar_ax, ax=ax,
             orientation='vertical', label=clabel, use_gridspec=True)


    # format colorbar ticks, labels etc
    if ctickslabels is None:
        ctickslabels = cticks
    else:
        assert len(ctickslabels)==len(cticks),\
            f"ctickslabels should have the same length as cticks ({len(cticks)})!" 
    if clabel is not None:
        cbar_ax.yaxis.label.set_font_properties(mpl.font_manager.FontProperties(family='arial', weight=clabel_w, size=clabel_s))
        cbar_ax.yaxis.label.set_rotation(-90)
        cbar_ax.yaxis.label.set_va('bottom')
        cbar_ax.yaxis.label.set_ha('center')
        cbar_ax.yaxis.labelpad = 5
    cbar_ax.yaxis.set_ticks(cticks)
    cbar_ax.yaxis.set_ticklabels(ctickslabels, ha='left')
    cbar_ax.yaxis.set_tick_params(pad=5, labelsize=cticks_s)
    cbar_ax.set_ylim(clim)

    fig.canvas.draw()
    set_ax_size(ax,*fig.get_size_inches())

    return fig


# Plot correlation matrix of variables x observations 2D array

def plot_cm(dp, units, cwin=100, cbin=0.2, b=5, corrEvaluator='CCG', vmax=5, vmin=0, cmap='viridis', periods='all',
            saveDir='~/Downloads', saveFig=False, _format='pdf', title=None, ret_cm=False):
    '''Plot correlation matrix.
    dp: datapath
    units: units list of the same dataset
    b: bin, in milliseconds'''

    # Sanity checks
    allowedCorEvals = ['CCG', 'covar', 'corrcoeff', 'corrcoeff_MB']
    try:
        assert corrEvaluator in allowedCorEvals
    except:
        print('WARNING: {} should be in {}. Exiting now.'.format(corrEvaluator, allowedCorEvals))
        return

    # Sort units by depth
    mainChans = get_depthSort_peakChans(dp, units)
    units, channels = mainChans[:,0], mainChans[:,1]

    # make correlation matrix of units sorted by depth
    cm = get_cm(dp, units, cbin, cwin, b, corrEvaluator, periods)

    # Plot correlation matrix
    ttl = f"Dataset: {dp.split('/')[-1]}" if title is None else title
    fig=imshow_cbar(cm, origin='top',
                xticks=np.arange(len(units)), yticks=np.arange(len(units)),
                xticklabels=[f'{units[i]}'for i in range(len(units))],
                yticklabels=[f'{units[i]}@{channels[i]}' for i in range(len(units))],
                xlabel=None, ylabel=None, title=ttl,
                cmapstr=cmap, vmin=vmin, vmax=vmax, colorseq='nonlinear',
                clabel='Crosscorr. [-0.5-0.5]ms (s.d.)', aspect='equal')

    if saveFig:
        if saveDir is None: saveDir=dp
        if title is None: title = None
        save_mpl_fig(fig, title, saveDir, _format)

    if ret_cm:
        return cm, units, channels # depth-sorted
    return fig

# Connectivity inferred from correlograms

def plot_sfcm(dp, corr_type='connections', metric='amp_z', cbin=0.5, cwin=100,
              p_th=0.02, n_consec_bins=3, fract_baseline=4./5, W_sd=10, test='Poisson_Stark',
              drop_seq=['sign', 'time', 'max_amplitude'], units=None, name=None,
              text=False, markers=False, ticks=True, depth_ticks=False,
              regions={}, reg_colors={}, vminmax=[-7,7], figsize=(4,4),
              saveFig=False, saveDir=None, _format='pdf',
              again=False, againCCG=False, use_template_for_peakchan=False, periods='all'):
    f'''
    Visually represents the connectivity matrix sfcm computed with npyx.corr.gen_sfc().
    Each line/row is a unit, sorted by depth, and the colormap corresponds to the 'metric' parameter.

    Arguments:
        - all parameters of npyx.corr.gen_sfc():
            {gen_sfc.__doc__}
    Returns:
        - fig: matplotlib figure
    '''

    sfc, sfcm, peakChs, sigstack, sigustack = gen_sfc(dp, corr_type, metric, cbin, cwin,
                                 p_th, n_consec_bins, fract_baseline, W_sd, test,
                                 again, againCCG, drop_seq, None, None, units=units, name=name,
                                 use_template_for_peakchan=use_template_for_peakchan,
                                 periods=periods)
    gu = peakChs[:,0]
    ch = peakChs[:,1].astype(np.int64)

    if corr_type=='synchrony':
        vminmax=[0,vminmax[1]]
    elif corr_type=='excitations':
        vminmax=[0,vminmax[1]]
    elif corr_type=='inhibitions':
        vminmax=[vminmax[0],0]

    if depth_ticks:
        labs=['{}'.format(3840-ch[i]*10) for i in range(len(gu)) if i%10==0]
        tks=[i for i in range(len(gu)) if i%10==0]
        lab = 'Depth on probe (\u03BCm)'
    else:
        labs=['{}@{}'.format(gu[i], ch[i]) for i in range(len(gu))]
        tks=np.arange(len(labs))
        if gu[0] == np.round(gu[0]):
            lab = 'unit@channel, depth-sorted.'
        else:
            lab = 'unit.dataset@channel, depth-sorted.'

    ttl='{}\n{}-{}-{}-{}-{}\n({})'.format(op.basename(dp),test, p_th, n_consec_bins, fract_baseline, W_sd, corr_type)
    dataset_borders = list(np.nonzero(np.diff(get_ds_ids(peakChs[:,0])))[0]) if assert_multi(dp) else []
    fig=imshow_cbar(sfcm, origin='top',
                xevents_toplot=dataset_borders, yevents_toplot=dataset_borders,
                events_color=[0.5,0.5,0.5],events_lw=1,
                xvalues=None, yvalues=None, xticks=tks, yticks=tks, title=ttl,
                xticklabels=labs, yticklabels=labs, xlabel=lab, ylabel=lab,
                cmapstr="RdBu_r", vmin=vminmax[0], vmax=vminmax[1], center=0, colorseq='nonlinear',
                clabel='Crosscorr. (zscore)', cticks=None,
                figsize=figsize, aspect='auto', function='imshow',
                ax=None)

    ax=fig.axes[0]
    ax.plot(ax.get_xlim(), ax.get_ylim()[::-1], ls="--", c=[0.5,0.5,0.5], lw=1)
    [ax.spines[sp].set_visible(True) for sp in ['left', 'bottom', 'top', 'right']]

    if not ticks:
        [tick.set_visible(False) for tick in ax.xaxis.get_major_ticks()]
        [tick.set_visible(False) for tick in ax.yaxis.get_major_ticks()]

    if any(regions):
        xl,yl=ax.get_xlim(), ax.get_ylim()
        if reg_colors=={}:
            reg_colors={k:(1,1,1) for k in regions.keys()}
        for region, rng in regions.items():
            rngi=[np.argmin(abs(r-ch)) for r in rng[::-1]]
            ax.plot([rngi[0]-0.5,rngi[0]-0.5], [yl[0],yl[1]], ls="-", c=[0.5,0.5,0.5], lw=0.5)
            ax.plot([rngi[1]+0.5,rngi[1]+0.5], [yl[0],yl[1]], ls="-", c=[0.5,0.5,0.5], lw=0.5)
            ax.plot([xl[0],xl[1]], [rngi[0]-0.5,rngi[0]-0.5], ls="-", c=[0.5,0.5,0.5], lw=0.5)
            ax.plot([xl[0],xl[1]], [rngi[1]+0.5,rngi[1]+0.5], ls="-", c=[0.5,0.5,0.5], lw=0.5)
            border_width = 2
            rect_y = mpl.patches.Rectangle((xl[0],rngi[0]-0.5), border_width, np.diff(rngi)+1, facecolor=reg_colors[region])
            rect_x = mpl.patches.Rectangle((rngi[0]-0.5, yl[0]-border_width), np.diff(rngi)+1, 100, facecolor=reg_colors[region])
            ax.add_patch(rect_y)
            ax.add_patch(rect_x)
            ax.text(x=border_width+1, y=rngi[0]+np.diff(rngi)/2, s=region, c=reg_colors[region],
                    fontsize=16, fontweight='bold', rotation=90, va='center')

    if markers:
        for i in range(sfcm.shape[0]):
            for j in range(sfcm.shape[0]):
                if i!=j:
                    ccgi=(gu[i]==sfc['uSrc'])&(gu[j]==sfc['uTrg'])
                    if np.any(ccgi):
                        pkT = sfc.loc[ccgi, 't_ms']
                        if pkT>0.5:
                            ax.scatter(j, i, marker='>', s=20, c="black")
                        elif pkT<-0.5:
                            ax.scatter(j, i, marker='<', s=20, c="black")
                        elif -0.5<=pkT and pkT<=0.5:
                            ax.scatter(j, i, marker='o', s=20, c="black")
    if text:
        for i in range(sfcm.shape[0]):
            for j in range(sfcm.shape[0]):
                ccgi=(gu[i]==sfc['uSrc'])&(gu[j]==sfc['uTrg'])
                if np.any(ccgi):
                    pkT = sfc.loc[ccgi, 't_ms']
                    if i!=j and (min(pkT)<=0 or max(pkT)>0):
                        ax.text(x=j, y=i, s=str(pkT), size=12)

    if saveFig:
        if saveDir is None: saveDir=dp
        ttl=ttl.replace('\n', '_')
        if name is not None: ttl=ttl+'_'+name
        save_mpl_fig(fig, ttl, saveDir, _format)

    return fig


#%% Save matplotlib animations
# https://towardsdatascience.com/how-to-create-animated-graphs-in-python-bb619cc2dec1
##### TO CREATE A SERIES OF PICTURES

def make_views(ax,angles,width, height, elevation=None,
                prefix='tmprot_',**kwargs):
    """
    Makes jpeg pictures of the given 3d ax, with different angles.
    Args:
        ax (3D axis): te ax
        angles (list): the list of angles (in degree) under which to
                       take the picture.
        width,height (float): size, in inches, of the output images.
        prefix (str): prefix for the files created.

    Returns: the list of files created (for later removal)
    """

    files = []
    ax.figure.set_size_inches(width,height)

    for i,angle in enumerate(angles):

        ax.view_init(elev = elevation, azim=angle)
        ax.set_xlim3d([206, 212])
        ax.set_ylim3d([208, 213])
        ax.set_zlim3d([207, 213])
        fname = '%s%03d.png'%(prefix,i)
        ax.figure.savefig(fname)
        files.append(fname)

    return files



##### TO TRANSFORM THE SERIES OF PICTURE INTO AN ANIMATION

def make_movie(files,output, fps=10,bitrate=1800,**kwargs):
    """
    Uses mencoder, produces a .mp4/.ogv/... movie from a list of
    picture files.
    """

    output_name, output_ext = os.path.splitext(output)
    command = { '.mp4' : 'mencoder "mf://%s" -mf fps=%d -o %s.mp4 -ovc lavc\
                         -lavcopts vcodec=msmpeg4v2:vbitrate=%d'
                         %(",".join(files),fps,output_name,bitrate)}

    command['.ogv'] = command['.mp4'] + '; ffmpeg -i %s.mp4 -r %d %s'%(output_name,fps,output)

    print(command[output_ext])
    output_ext = os.path.splitext(output)[1]
    os.system(command[output_ext])



def make_gif(files,output,delay=100, repeat=True,**kwargs):
    """
    Uses imageMagick to produce an animated .gif from a list of
    picture files.
    """

    loop = -1 if repeat else 0
    os.system('convert -delay %d -loop %d %s %s'
              %(delay,loop," ".join(files),output))




def make_strip(files,output,**kwargs):
    """
    Uses imageMagick to produce a .jpeg strip from a list of
    picture files.
    """

    os.system('montage -tile 1x -geometry +0+0 %s %s'%(" ".join(files),output))



##### MAIN FUNCTION

def rotanimate(ax, width, height, angles, output, **kwargs):
    """
    Produces an animation (.mp4,.ogv,.gif,.jpeg,.png) from a 3D plot on
    a 3D ax

    Args:
        ax (3D axis): the ax containing the plot of interest
        angles (list): the list of angles (in degree) under which to
                       show the plot.
        output : name of the output file. The extension determines the
                 kind of animation used.
        **kwargs:
            - width : in inches
            - heigth: in inches
            - framerate : frames per second
            - delay : delay between frames in milliseconds
            - repeat : True or False (.gif only)
    """

    output_ext = os.path.splitext(output)[1]

    files = make_views(ax,angles, width, height, **kwargs)

    D = { '.mp4' : make_movie,
          '.ogv' : make_movie,
          '.gif': make_gif ,
          '.jpeg': make_strip,
          '.png':make_strip}

    D[output_ext](files,output,**kwargs)

    for f in files:
        os.remove(f)

def make_mpl_animation(ax, Nangles, delay, width=10, height=10, saveDir='~/Downloads', title='movie', frmt='gif', axis=True):
    '''
    ax is the figure axes that you will make rotate along its vertical axis,
    on Nangles angles (default 300),
    separated by delay time units (default 2),
    at a resolution of widthxheight pixels (default 10x10),
    saved in saveDir directory (default Downloads) with the title title (default movie) and format frmt (gif).
    '''
    assert frmt in ['gif', 'mp4', 'ogv']
    if not axis: plt.axis('off') # remove axes for visual appeal
    oldDir=os.getcwd()
    saveDir=op.expanduser(saveDir)
    os.chdir(saveDir)
    angles = np.linspace(0,360,Nangles)[:-1] # Take 20 angles between 0 and 360
    ttl='{}.{}'.format(title, frmt)
    rotanimate(ax, width, height, angles,ttl, delay=delay)

    os.chdir(oldDir)


def plot_filtered_times(dp, unit, first_n_minutes=20, consecutive_n_seconds = 180, acg_window_len=3, acg_chunk_size = 10, gauss_window_len = 3, gauss_chunk_size = 10, use_or_operator = False):
    unit_size_s = first_n_minutes * 60

    goodsec, acgsec, gausssec = train_quality(dp, unit, first_n_minutes, consecutive_n_seconds, acg_window_len, acg_chunk_size, gauss_window_len, gauss_chunk_size, use_or_operator)

    good_sec = []
    for i in goodsec:
        good_sec.append(list(range(i[0], i[1]+1)))
    good_sec = np.hstack((good_sec))

    acg_sec = []
    for i in acgsec:
        acg_sec.append(list(range(i[0], i[1]+1)))
    acg_sec = np.hstack((acg_sec))

    gauss_sec = []
    for i in gausssec:
        gauss_sec.append(list(range(i[0], i[1]+1)))
    gauss_sec = np.hstack((gauss_sec))

    # Parameters
    fs = read_metadata(dp)['highpass']['sampling_rate']

    samples_fr = unit_size_s * fs
    spike_clusters = np.load(dp/'spike_clusters.npy')
    amplitudes_sample = np.load(dp/'amplitudes.npy')  # shape N_tot_spikes x 1
    spike_times = np.load(dp/'spike_times.npy')  # in samples

    amplitudes_unit = amplitudes_sample[spike_clusters == unit]
    spike_times_unit = spike_times[spike_clusters == unit]
    unit_mask_20 = (spike_times_unit <= samples_fr)
    spike_times_unit_20 = spike_times_unit[unit_mask_20]
    amplitudes_unit_20 = amplitudes_unit[unit_mask_20]


    plt.figure()
    plt.plot(spike_times_unit_20/fs, amplitudes_unit_20, '.', alpha = 0.5)
    plt.text(0, 3,'Gaussian FN', fontsize = 5, color = 'blue')
    plt.text(0, 1,'FP + FN', fontsize = 5, color = 'green')
    plt.text(0, -3,'ACG FP', fontsize = 5, color = 'red')
    plt.title(f"Amplitudes in first 20 min for {unit}")

    for i in good_sec:
        s_time, e_time = i ,(i+1)
        plt.hlines(0, s_time, e_time, color = 'green')
#     # find the longest consecutive section
# # check if this is longer than 3 minutes, 18 sections
#
    for i in acg_sec:
        s_time, e_time = i ,(i+1)
        plt.hlines(-2, s_time, e_time, color = 'red')
#
    for i in gauss_sec:
        s_time, e_time = i ,(i+1)
        plt.hlines(2, s_time, e_time, color = 'blue')
    plt.show()
