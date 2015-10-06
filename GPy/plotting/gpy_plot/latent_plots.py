#===============================================================================
# Copyright (c) 2015, Max Zwiessele
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of GPy.plotting.gpy_plot.latent_plots nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#===============================================================================
import numpy as np
from . import pl
from .plot_util import get_x_y_var, get_which_data_ycols,\
    get_which_data_rows, update_not_existing_kwargs, helper_predict_with_model,\
    helper_for_plot_data, scatter_label_generator, subsample_X,\
    find_best_layout_for_subplots

def _wait_for_updates(view, updates):
    try:
        if updates:
            clear = raw_input('yes or enter to deactivate updates - otherwise still do updates - use plots[imshow].deactivate() to clear')
            if clear.lower() in 'yes' or clear == '':
                view.deactivate()
        else:
            view.deactivate()
    except AttributeError:
        # No updateable view:
        pass
            

def plot_prediction_fit(self, plot_limits=None,
        which_data_rows='all', which_data_ycols='all', 
        fixed_inputs=None, resolution=None,
        plot_raw=False, apply_link=False, visible_dims=None,
        predict_kw=None, scatter_kwargs=None, **plot_kwargs):
    """
    Plot the fit of the (Bayesian)GPLVM latent space prediction to the outputs.
    This scatters two output dimensions against each other and a line
    from the prediction in two dimensions between them.
    
    Give the Y_metadata in the predict_kw if you need it.
    
    :param which_data_rows: which of the training data to plot (default all)
    :type which_data_rows: 'all' or a slice object to slice self.X, self.Y
    :param array-like which_data_ycols: which columns of y to plot (array-like or list of ints)
    :param fixed_inputs: a list of tuple [(i,v), (i,v)...], specifying that input dimension i should be set to value v.
    :type fixed_inputs: a list of tuples
    :param int resolution: The resolution of the prediction [defaults are 1D:200, 2D:50]
    :param bool plot_raw: plot the latent function (usually denoted f) only?
    :param bool apply_link: whether to apply the link function of the GP to the raw prediction.
    :param array-like visible_dims: which columns of the input X (!) to plot (array-like or list of ints)
    :param dict predict_kw: the keyword arguments for the prediction. If you want to plot a specific kernel give dict(kern=<specific kernel>) in here
    :param dict sactter_kwargs: kwargs for the scatter plot, specific for the plotting library you are using
    :param kwargs plot_kwargs: kwargs for the data plot for the plotting library you are using
    """
    canvas, kwargs = pl.get_new_canvas(**plot_kwargs)
    plots = _plot_prediction_fit(self, canvas, plot_limits, which_data_rows, which_data_ycols, 
                                 fixed_inputs, resolution, plot_raw, 
                                 apply_link, visible_dims,
                                 predict_kw, scatter_kwargs, **kwargs)
    return pl.show_canvas(canvas, plots)

def _plot_prediction_fit(self, canvas, plot_limits=None,
        which_data_rows='all', which_data_ycols='all', 
        fixed_inputs=None, resolution=None,
        plot_raw=False, apply_link=False, visible_dims=False,
        predict_kw=None, scatter_kwargs=None, **plot_kwargs):
    
    ycols = get_which_data_ycols(self, which_data_ycols)
    rows = get_which_data_rows(self, which_data_rows)

    if visible_dims is None:
        visible_dims = self.get_most_significant_input_dimensions()[:1]

    X, _, Y, _, free_dims, Xgrid, _, _, _, _, resolution = helper_for_plot_data(self, plot_limits, visible_dims, fixed_inputs, resolution)
    
    plots = {}
    
    if len(free_dims)<2:
        if len(free_dims)==1:
            if scatter_kwargs is None:
                scatter_kwargs = {}
            update_not_existing_kwargs(scatter_kwargs, pl.defaults.data_y_1d)  # @UndefinedVariable
            plots['output'] = pl.scatter(canvas, Y[rows, ycols[0]], Y[rows, ycols[1]],
                                      color=X[rows, free_dims[0]],
                                      **scatter_kwargs)
            if predict_kw is None:
                predict_kw = {}
            mu, _, _ = helper_predict_with_model(self, Xgrid, plot_raw, 
                                              apply_link, None, 
                                              ycols, predict_kw)
            update_not_existing_kwargs(plot_kwargs, pl.defaults.data_y_1d_plot)  # @UndefinedVariable
            plots['output_fit'] = pl.plot(canvas, mu[:, 0], mu[:, 1], **plot_kwargs)
        else:
            pass #Nothing to plot!
    else:
        raise NotImplementedError("Cannot plot in more then one dimension.")
    return plots

def _plot_latent_scatter(self, canvas, X, visible_dims, labels, marker, num_samples, projection='2d', **kwargs):
    from .. import Tango
    Tango.reset()
    if labels is None:
        labels = np.ones(self.num_data)
    X, labels = subsample_X(X, labels, num_samples)
    scatters = []    
    for x, y, z, this_label, _, m in scatter_label_generator(labels, X, visible_dims, marker):
        update_not_existing_kwargs(kwargs, pl.defaults.latent_scatter)
        scatters.append(pl.scatter(canvas, x, y, Z=z, marker=m, color=Tango.nextMedium(), label=this_label, **kwargs))
    return scatters

def plot_latent_scatter(self, labels=None, 
                        which_indices=None,
                        legend=True,
                        plot_limits=None,
                        marker='<>^vsd', 
                        num_samples=1000,
                        projection='2d',
                        **kwargs):
    """
    Plot a scatter plot of the latent space.
    
    :param array-like labels: a label for each data point (row) of the inputs
    :param (int, int) which_indices: which input dimensions to plot against each other
    :param bool legend: whether to plot the legend on the figure
    :param plot_limits: the plot limits for the plot
    :type plot_limits: (xmin, xmax, ymin, ymax) or ((xmin, xmax), (ymin, ymax))
    :param str marker: markers to use - cycle if more labels then markers are given
    :param kwargs: the kwargs for the scatter plots
    """    
    sig_dims = self.get_most_significant_input_dimensions(which_indices)
    input_1, input_2, input_3 = [i for i in sig_dims if i is not None]

    canvas, kwargs = pl.get_new_canvas(projection=projection, **kwargs)
    X, _, _ = get_x_y_var(self)
    scatters = _plot_latent_scatter(self, canvas, X, sig_dims, labels, marker, num_samples, projection=projection, **kwargs)
    if projection == '3d':
        return pl.show_canvas(canvas, dict(scatter=scatters), legend=legend and (labels is not None),
                              xlabel='latent dimension %i' % input_1, 
                              ylabel='latent dimension %i' % input_2,
                              zlabel='latent dimension %i' % input_3)
    else:
        return pl.show_canvas(canvas, dict(scatter=scatters), legend=legend and (labels is not None),
                              xlabel='latent dimension %i' % input_1, 
                              ylabel='latent dimension %i' % input_2,
                              #zlabel='latent dimension %i' % input_3
                              )


def _plot_magnification(self, canvas, input_1, input_2, Xgrid, 
                        xmin, xmax, resolution,
                        mean=True, covariance=True, 
                        kern=None,  
                        **imshow_kwargs):
    def plot_function(x):
        Xtest_full = np.zeros((x.shape[0], Xgrid.shape[1]))
        Xtest_full[:, [input_1, input_2]] = x
        mf = self.predict_magnification(Xtest_full, kern=kern, mean=mean, covariance=covariance)
        return mf.reshape(resolution, resolution).T
    imshow_kwargs = update_not_existing_kwargs(imshow_kwargs, pl.defaults.magnification)
    Y = plot_function(Xgrid[:, [input_1, input_2]])
    view = pl.imshow(canvas, Y, 
                     (xmin[0], xmax[0], xmin[1], xmax[1]), 
                     None, plot_function, resolution,
                     vmin=Y.min(), vmax=Y.max(), 
                     **imshow_kwargs)
    return view
    
def plot_magnification(self, labels=None, which_indices=None,
                resolution=60, marker='<>^vsd', legend=True,
                plot_limits=None,
                updates=False, 
                mean=True, covariance=True, 
                kern=None, num_samples=1000,
                scatter_kwargs=None, **imshow_kwargs):
    """
    Plot the magnification factor of the GP on the inputs. This is the 
    density of the GP as a gray scale.
    
    :param array-like labels: a label for each data point (row) of the inputs
    :param (int, int) which_indices: which input dimensions to plot against each other
    :param int resolution: the resolution at which we predict the magnification factor
    :param str marker: markers to use - cycle if more labels then markers are given
    :param bool legend: whether to plot the legend on the figure
    :param plot_limits: the plot limits for the plot
    :type plot_limits: (xmin, xmax, ymin, ymax) or ((xmin, xmax), (ymin, ymax))
    :param bool updates: if possible, make interactive updates using the specific library you are using
    :param bool mean: use the mean of the Wishart embedding for the magnification factor
    :param bool covariance: use the covariance of the Wishart embedding for the magnification factor
    :param :py:class:`~GPy.kern.Kern` kern: the kernel to use for prediction
    :param int num_samples: the number of samples to plot maximally. We do a stratified subsample from the labels, if the number of samples (in X) is higher then num_samples. 
    :param imshow_kwargs: the kwargs for the imshow (magnification factor)
    :param kwargs: the kwargs for the scatter plots
    """
    input_1, input_2 = self.get_most_significant_input_dimensions(which_indices)
    canvas, imshow_kwargs = pl.get_new_canvas(**imshow_kwargs)
    X, _, _, _, _, Xgrid, _, _, xmin, xmax, resolution = helper_for_plot_data(self, plot_limits, (input_1, input_2), None, resolution)    
    scatters = _plot_latent_scatter(self, canvas, X, input_1, input_2, labels, marker, num_samples, **scatter_kwargs or {})
    view = _plot_magnification(self, canvas, input_1, input_2, Xgrid, xmin, xmax, resolution, mean, covariance, kern, **imshow_kwargs)
    if (legend is True) and (labels is not None):
        legend = find_best_layout_for_subplots(len(np.unique(labels)))[1]
    plots = pl.show_canvas(canvas, dict(scatter=scatters, imshow=view), 
                           legend=legend, 
                           xlim=(xmin[0], xmax[0]), ylim=(xmin[1], xmax[1]),
                           xlabel='latent dimension %i' % input_1, ylabel='latent dimension %i' % input_2)
    _wait_for_updates(view, updates)
    return plots




def _plot_latent(self, canvas, input_1, input_2, Xgrid, 
                        xmin, xmax, resolution,
                        kern=None,  
                        **imshow_kwargs):
    def plot_function(x):
        Xtest_full = np.zeros((x.shape[0], Xgrid.shape[1]))
        Xtest_full[:, [input_1, input_2]] = x
        mf = np.log(self.predict(Xtest_full, kern=kern)[1])
        return mf.reshape(resolution, resolution).T

    imshow_kwargs = update_not_existing_kwargs(imshow_kwargs, pl.defaults.latent)
    Y = plot_function(Xgrid[:, [input_1, input_2]]).reshape(resolution, resolution).T
    view = pl.imshow(canvas, Y, 
                     (xmin[0], xmax[0], xmin[1], xmax[1]), 
                     None, plot_function, resolution,
                     vmin=Y.min(), vmax=Y.max(), 
                     **imshow_kwargs)
    return view

def plot_latent(self, labels=None, which_indices=None,
                resolution=60, legend=True,
                plot_limits=None,
                updates=False, 
                kern=None, marker='<>^vsd', 
                num_samples=1000,
                scatter_kwargs=None, **imshow_kwargs):
    """
    Plot the latent space of the GP on the inputs. This is the 
    density of the GP posterior as a grey scale and the 
    scatter plot of the input dimemsions selected by which_indices.
    
    :param array-like labels: a label for each data point (row) of the inputs
    :param (int, int) which_indices: which input dimensions to plot against each other
    :param int resolution: the resolution at which we predict the magnification factor
    :param bool legend: whether to plot the legend on the figure
    :param plot_limits: the plot limits for the plot
    :type plot_limits: (xmin, xmax, ymin, ymax) or ((xmin, xmax), (ymin, ymax))
    :param bool updates: if possible, make interactive updates using the specific library you are using
    :param :py:class:`~GPy.kern.Kern` kern: the kernel to use for prediction
    :param str marker: markers to use - cycle if more labels then markers are given
    :param int num_samples: the number of samples to plot maximally. We do a stratified subsample from the labels, if the number of samples (in X) is higher then num_samples. 
    :param imshow_kwargs: the kwargs for the imshow (magnification factor)
    :param scatter_kwargs: the kwargs for the scatter plots
    """
    input_1, input_2 = self.get_most_significant_input_dimensions(which_indices)
    canvas, imshow_kwargs = pl.get_new_canvas(**imshow_kwargs)
    X, _, _, _, _, Xgrid, _, _, xmin, xmax, resolution = helper_for_plot_data(self, plot_limits, (input_1, input_2), None, resolution)    
    scatters = _plot_latent_scatter(self, canvas, X, input_1, input_2, labels, marker, num_samples, **scatter_kwargs or {})
    view = _plot_latent(self, canvas, input_1, input_2, Xgrid, xmin, xmax, resolution, kern, **imshow_kwargs)
    if (legend is True) and (labels is not None):
        legend = find_best_layout_for_subplots(len(np.unique(labels)))[1]
    plots = pl.show_canvas(canvas, dict(scatter=scatters, imshow=view), 
                           legend=legend, 
                           xlim=(xmin[0], xmax[0]), ylim=(xmin[1], xmax[1]),
                           xlabel='latent dimension %i' % input_1, ylabel='latent dimension %i' % input_2)
    _wait_for_updates(view, updates)
    return plots

def _plot_steepest_gradient_map(self, canvas, input_1, input_2, Xgrid, 
                        xmin, xmax, resolution, output_labels,
                        kern=None, annotation_kwargs=None, 
                        **imshow_kwargs):
    if output_labels is None:
        output_labels = range(self.output_dim)
    def plot_function(x):
        Xgrid[:, [input_1, input_2]] = x
        dmu_dX = self.predictive_gradients(Xgrid, kern=kern)[0].sum(1)
        argmax = np.argmax(dmu_dX, 1).astype(int)
        return dmu_dX.max(1).reshape(resolution, resolution).T, np.array(output_labels)[argmax].reshape(resolution, resolution)
    Y, annotation = plot_function(Xgrid[:, [input_1, input_2]])
    annotation_kwargs = update_not_existing_kwargs(annotation_kwargs or {}, pl.defaults.annotation)
    imshow_kwargs = update_not_existing_kwargs(imshow_kwargs or {}, pl.defaults.gradient)
    imshow, annotation = pl.annotation_heatmap(canvas, Y, annotation, 
                                               (xmin[0], xmax[0], xmin[1], xmax[1]), 
                                               None, plot_function, resolution, 
                                               imshow_kwargs=imshow_kwargs, **annotation_kwargs)
    return dict(heatmap=imshow, annotation=annotation)

def plot_steepest_gradient_map(self, output_labels=None, data_labels=None, which_indices=None,
                resolution=15, legend=True,
                plot_limits=None,
                updates=False, 
                kern=None, marker='<>^vsd', 
                num_samples=1000,
                annotation_kwargs=None, scatter_kwargs=None, **imshow_kwargs):

    """
    Plot the latent space of the GP on the inputs. This is the 
    density of the GP posterior as a grey scale and the 
    scatter plot of the input dimemsions selected by which_indices.
    
    :param array-like labels: a label for each data point (row) of the inputs
    :param (int, int) which_indices: which input dimensions to plot against each other
    :param int resolution: the resolution at which we predict the magnification factor
    :param bool legend: whether to plot the legend on the figure, if int plot legend columns on legend
    :param plot_limits: the plot limits for the plot
    :type plot_limits: (xmin, xmax, ymin, ymax) or ((xmin, xmax), (ymin, ymax))
    :param bool updates: if possible, make interactive updates using the specific library you are using
    :param :py:class:`~GPy.kern.Kern` kern: the kernel to use for prediction
    :param str marker: markers to use - cycle if more labels then markers are given
    :param int num_samples: the number of samples to plot maximally. We do a stratified subsample from the labels, if the number of samples (in X) is higher then num_samples. 
    :param imshow_kwargs: the kwargs for the imshow (magnification factor)
    :param annotation_kwargs: the kwargs for the annotation plot
    :param scatter_kwargs: the kwargs for the scatter plots
    """
    input_1, input_2 = self.get_most_significant_input_dimensions(which_indices)
    canvas, imshow_kwargs = pl.get_new_canvas(**imshow_kwargs)
    X, _, _, _, _, Xgrid, _, _, xmin, xmax, resolution = helper_for_plot_data(self, plot_limits, (input_1, input_2), None, resolution)    
    plots = dict(scatter=_plot_latent_scatter(self, canvas, X, input_1, input_2, data_labels, marker, num_samples, **scatter_kwargs or {}))
    plots.update(_plot_steepest_gradient_map(self, canvas, input_1, input_2, Xgrid, xmin, xmax, resolution, output_labels, kern, annotation_kwargs=annotation_kwargs, **imshow_kwargs))
    if (legend is True) and (data_labels is not None):
        legend = find_best_layout_for_subplots(len(np.unique(data_labels)))[1]
    pl.show_canvas(canvas, plots, legend=legend, 
                           xlim=(xmin[0], xmax[0]), ylim=(xmin[1], xmax[1]),
                           xlabel='latent dimension %i' % input_1, ylabel='latent dimension %i' % input_2)
    _wait_for_updates(plots['annotation'], updates)
    return plots





