/* -*- Mode: C; tab-width: 8; indent-tabs-mode: t; c-basic-offset: 8 -*-
 *
 * Copyright (C) 2008-2009 Richard Hughes <richard@hughsie.com>
 *
 * Licensed under the GNU Lesser General Public License Version 2.1
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
 */

#include "config.h"

#include <stdio.h>
#include <string.h>
#include <gio/gio.h>
#include <glib.h>
#include <packagekit-glib2/pk-results.h>
#include <packagekit-glib2/pk-task.h>
#include <packagekit-glib2/pk-progress.h>

#include "pk-task-sync.h"

/* tiny helper to help us do the async operation */
typedef struct {
	GError		**error;
	GMainContext	*context;
	GMainLoop	*loop;
	PkResults	*results;
} PkTaskHelper;

/*
 * pk_task_generic_finish_sync:
 **/
static void
pk_task_generic_finish_sync (PkTask *task, GAsyncResult *res, PkTaskHelper *helper)
{
	PkResults *results;
	/* get the result */
	results = pk_task_generic_finish (task, res, helper->error);
	if (results != NULL) {
		g_object_unref (results);
		helper->results = g_object_ref (results);
	}
	g_main_loop_quit (helper->loop);
}

/**
 * pk_task_remove_packages_sync:
 * @task: a valid #PkTask instance
 * @package_ids: (array zero-terminated=1): a null terminated array of package_id structures such as "hal;0.0.1;i386;fedora"
 * @allow_deps: if other dependent packages are allowed to be removed from the computer
 * @autoremove: if other packages installed at the same time should be tried to remove
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Remove a package (optionally with dependancies) from the system.
 * If @allow_deps is set to %FALSE, and other packages would have to be removed,
 * then the transaction would fail.
 *
 * Warning: this function is synchronous, and may block. Do not use it in GUI
 * applications.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.5.3
 **/
PkResults *
pk_task_remove_packages_sync (PkTask *task, gchar **package_ids, gboolean allow_deps, gboolean autoremove, GCancellable *cancellable,
			      PkProgressCallback progress_callback, gpointer progress_user_data, GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_remove_packages_async (task, package_ids, allow_deps, autoremove, cancellable, progress_callback, progress_user_data,
				       (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_install_packages_sync:
 * @task: a valid #PkTask instance
 * @package_ids: (array zero-terminated=1): a null terminated array of package_id structures such as "hal;0.0.1;i386;fedora"
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Install a package of the newest and most correct version.
 *
 * Warning: this function is synchronous, and may block. Do not use it in GUI
 * applications.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.5.3
 **/
PkResults *
pk_task_install_packages_sync (PkTask *task, gchar **package_ids, GCancellable *cancellable,
			       PkProgressCallback progress_callback, gpointer progress_user_data, GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_install_packages_async (task, package_ids, cancellable, progress_callback, progress_user_data,
					(GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_update_packages_sync:
 * @task: a valid #PkTask instance
 * @package_ids: (array zero-terminated=1): a null terminated array of package_id structures such as "hal;0.0.1;i386;fedora"
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Update specific packages to the newest available versions.
 *
 * Warning: this function is synchronous, and may block. Do not use it in GUI
 * applications.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.5.3
 **/
PkResults *
pk_task_update_packages_sync (PkTask *task, gchar **package_ids, GCancellable *cancellable,
			      PkProgressCallback progress_callback, gpointer progress_user_data, GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_update_packages_async (task, package_ids, cancellable, progress_callback, progress_user_data,
				       (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_install_files_sync:
 * @task: a valid #PkTask instance
 * @files: (array zero-terminated=1): a file such as "/home/hughsie/Desktop/hal-devel-0.10.0.rpm"
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Install a file locally, and get the deps from the repositories.
 * This is useful for double clicking on a .rpm or .deb file.
 *
 * Warning: this function is synchronous, and may block. Do not use it in GUI
 * applications.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.5.3
 **/
PkResults *
pk_task_install_files_sync (PkTask *task, gchar **files, GCancellable *cancellable,
			    PkProgressCallback progress_callback, gpointer progress_user_data, GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_install_files_async (task, files, cancellable, progress_callback, progress_user_data,
				     (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_resolve_sync:
 * @task: a valid #PkTask instance
 * @filters: a bitfield of filters that can be used to limit the results
 * @packages: (array zero-terminated=1): package names to find
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Resolves a package name to a package-id.
 *
 * Since: 0.6.5
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 **/
PkResults *
pk_task_resolve_sync (PkTask *task, PkBitfield filters, gchar **packages, GCancellable *cancellable,
		      PkProgressCallback progress_callback, gpointer progress_user_data,
		      GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_resolve_async (task, filters, packages, cancellable, progress_callback, progress_user_data,
			       (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_search_names_sync:
 * @task: a valid #PkTask instance
 * @filters: a bitfield of filters that can be used to limit the results
 * @values: (array zero-terminated=1): search values
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Searches for a package name.
 *
 * Since: 0.6.5
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 **/
PkResults *
pk_task_search_names_sync (PkTask *task, PkBitfield filters, gchar **values, GCancellable *cancellable,
			   PkProgressCallback progress_callback, gpointer progress_user_data,
			   GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_search_names_async (task, filters, values, cancellable, progress_callback, progress_user_data,
				    (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_search_details_sync:
 * @task: a valid #PkTask instance
 * @filters: a bitfield of filters that can be used to limit the results
 * @values: (array zero-terminated=1): search values
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Searches for some package details.
 *
 * Since: 0.6.5
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 **/
PkResults *
pk_task_search_details_sync (PkTask *task, PkBitfield filters, gchar **values, GCancellable *cancellable,
			     PkProgressCallback progress_callback, gpointer progress_user_data,
			     GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_search_details_async (task, filters, values, cancellable, progress_callback, progress_user_data,
				      (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_search_groups_sync:
 * @task: a valid #PkTask instance
 * @filters: a bitfield of filters that can be used to limit the results
 * @values: (array zero-terminated=1): search values
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Searches the group lists.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.6.5
 **/
PkResults *
pk_task_search_groups_sync (PkTask *task, PkBitfield filters, gchar **values, GCancellable *cancellable,
			    PkProgressCallback progress_callback, gpointer progress_user_data,
			    GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_search_groups_async (task, filters, values, cancellable, progress_callback, progress_user_data,
				     (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_search_files_sync:
 * @task: a valid #PkTask instance
 * @filters: a bitfield of filters that can be used to limit the results
 * @values: (array zero-terminated=1): search values
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Searches for specific files.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.6.5
 **/
PkResults *
pk_task_search_files_sync (PkTask *task, PkBitfield filters, gchar **values, GCancellable *cancellable,
			   PkProgressCallback progress_callback, gpointer progress_user_data,
			   GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_search_files_async (task, filters, values, cancellable, progress_callback, progress_user_data,
				    (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_get_details_sync:
 * @task: a valid #PkTask instance
 * @package_ids: (array zero-terminated=1): a null terminated array of package_id structures such as "hal;0.0.1;i386;fedora"
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Gets details about packages.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.6.5
 **/
PkResults *
pk_task_get_details_sync (PkTask *task, gchar **package_ids, GCancellable *cancellable,
			  PkProgressCallback progress_callback, gpointer progress_user_data,
			  GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_get_details_async (task, package_ids, cancellable, progress_callback, progress_user_data,
				   (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_get_update_detail_sync:
 * @task: a valid #PkTask instance
 * @package_ids: (array zero-terminated=1): a null terminated array of package_id structures such as "hal;0.0.1;i386;fedora"
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Gets details about updates.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.6.5
 **/
PkResults *
pk_task_get_update_detail_sync (PkTask *task, gchar **package_ids, GCancellable *cancellable,
				PkProgressCallback progress_callback, gpointer progress_user_data,
				GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_get_update_detail_async (task, package_ids, cancellable, progress_callback, progress_user_data,
				         (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_download_packages_sync:
 * @task: a valid #PkTask instance
 * @package_ids: (array zero-terminated=1): a null terminated array of package_id structures such as "hal;0.0.1;i386;fedora"
 * @directory: the destination directory
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Downloads packages
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.6.5
 **/
PkResults *
pk_task_download_packages_sync (PkTask *task, gchar **package_ids, const gchar *directory, GCancellable *cancellable,
				PkProgressCallback progress_callback, gpointer progress_user_data,
				GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_download_packages_async (task, package_ids, directory, cancellable, progress_callback, progress_user_data,
				         (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_get_updates_sync:
 * @task: a valid #PkTask instance
 * @filters: a bitfield of filters that can be used to limit the results
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Gets the update lists.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.6.5
 **/
PkResults *
pk_task_get_updates_sync (PkTask *task, PkBitfield filters, GCancellable *cancellable,
			  PkProgressCallback progress_callback, gpointer progress_user_data,
			  GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_get_updates_async (task, filters, cancellable, progress_callback, progress_user_data,
				     (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_depends_on_sync:
 * @task: a valid #PkTask instance
 * @filters: a bitfield of filters that can be used to limit the results
 * @package_ids: (array zero-terminated=1): a null terminated array of package_id structures such as "hal;0.0.1;i386;fedora"
 * @recursive: if we should recurse to packages that depend on other packages
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Get the list of dependent packages.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.6.5
 **/
PkResults *
pk_task_depends_on_sync (PkTask *task, PkBitfield filters, gchar **package_ids, gboolean recursive, GCancellable *cancellable,
			  PkProgressCallback progress_callback, gpointer progress_user_data,
			  GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_depends_on_async (task, filters, package_ids, recursive, cancellable, progress_callback, progress_user_data,
				     (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_get_packages_sync:
 * @task: a valid #PkTask instance
 * @filters: a bitfield of filters that can be used to limit the results
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Gets the list of packages.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.6.5
 **/
PkResults *
pk_task_get_packages_sync (PkTask *task, PkBitfield filters, GCancellable *cancellable,
			   PkProgressCallback progress_callback, gpointer progress_user_data,
			   GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_get_packages_async (task, filters, cancellable, progress_callback, progress_user_data,
				    (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_required_by_sync:
 * @task: a valid #PkTask instance
 * @filters: a bitfield of filters that can be used to limit the results
 * @package_ids: (array zero-terminated=1): a null terminated array of package_id structures such as "hal;0.0.1;i386;fedora"
 * @recursive: if we should return packages that depend on the ones we do
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Get the packages this package requires.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.6.5
 **/
PkResults *
pk_task_required_by_sync (PkTask *task, PkBitfield filters, gchar **package_ids, gboolean recursive, GCancellable *cancellable,
			   PkProgressCallback progress_callback, gpointer progress_user_data,
			   GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_required_by_async (task, filters, package_ids, recursive, cancellable, progress_callback, progress_user_data,
				    (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_what_provides_sync:
 * @task: a valid #PkTask instance
 * @filters: a bitfield of filters that can be used to limit the results
 * @values: (array zero-terminated=1): values to search for
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Find the package that provides some resource.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.6.5
 **/
PkResults *
pk_task_what_provides_sync (PkTask *task, PkBitfield filters,
			    gchar **values, GCancellable *cancellable,
			    PkProgressCallback progress_callback, gpointer progress_user_data,
			    GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_what_provides_async (task, filters, values, cancellable, progress_callback, progress_user_data,
				     (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_get_files_sync:
 * @task: a valid #PkTask instance
 * @package_ids: (array zero-terminated=1): a null terminated array of package_id structures such as "hal;0.0.1;i386;fedora"
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Get the files in a package.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.6.5
 **/
PkResults *
pk_task_get_files_sync (PkTask *task, gchar **package_ids, GCancellable *cancellable,
			PkProgressCallback progress_callback, gpointer progress_user_data,
			GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_get_files_async (task, package_ids, cancellable, progress_callback, progress_user_data,
				 (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_get_categories_sync:
 * @task: a valid #PkTask instance
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Get the categories available.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.6.5
 **/
PkResults *
pk_task_get_categories_sync (PkTask *task, GCancellable *cancellable,
			     PkProgressCallback progress_callback, gpointer progress_user_data,
			     GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_get_categories_async (task, cancellable, progress_callback, progress_user_data,
				      (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_refresh_cache_sync:
 * @task: a valid #PkTask instance
 * @force: if the metadata should be deleted and re-downloaded even if it is correct
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Refresh the package cache.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.6.5
 **/
PkResults *
pk_task_refresh_cache_sync (PkTask *task, gboolean force, GCancellable *cancellable,
			    PkProgressCallback progress_callback, gpointer progress_user_data,
			    GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_refresh_cache_async (task, force, cancellable, progress_callback, progress_user_data,
				     (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_get_repo_list_sync:
 * @task: a valid #PkTask instance
 * @filters: a bitfield of filters that can be used to limit the results
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Get the list of available repositories.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.6.5
 **/
PkResults *
pk_task_get_repo_list_sync (PkTask *task, PkBitfield filters, GCancellable *cancellable,
			    PkProgressCallback progress_callback, gpointer progress_user_data,
			    GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_get_repo_list_async (task, filters, cancellable, progress_callback, progress_user_data,
				     (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_repo_enable_sync:
 * @task: a valid #PkTask instance
 * @repo_id: The software repository ID
 * @enabled: %TRUE or %FALSE
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Enable or disable a specific repo.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.6.5
 **/
PkResults *
pk_task_repo_enable_sync (PkTask *task, const gchar *repo_id, gboolean enabled, GCancellable *cancellable,
			  PkProgressCallback progress_callback, gpointer progress_user_data,
			  GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_repo_enable_async (task, repo_id, enabled, cancellable, progress_callback, progress_user_data,
				   (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_upgrade_system_sync:
 * @task: a valid #PkTask instance
 * @distro_id: a distro ID such as "fedora-14"
 * @upgrade_kind: a #PkUpgradeKindEnum such as %PK_UPGRADE_KIND_ENUM_COMPLETE
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * This transaction will update the distro to the next version, which may
 * involve just downloading the installer and setting up the boot device,
 * or may involve doing an on-line upgrade.
 *
 * The backend will decide what is best to do.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 1.0.12
 **/
PkResults *
pk_task_upgrade_system_sync (PkTask *task,
                             const gchar *distro_id,
                             PkUpgradeKindEnum upgrade_kind,
                             GCancellable *cancellable,
                             PkProgressCallback progress_callback, gpointer progress_user_data, GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_upgrade_system_async (task, distro_id, upgrade_kind, cancellable, progress_callback, progress_user_data,
				      (GAsyncReadyCallback) pk_task_generic_finish_sync, &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}

/**
 * pk_task_repair_system_sync:
 * @task: a valid #PkTask instance
 * @cancellable: a #GCancellable or %NULL
 * @progress_callback: (scope call): the function to run when the progress changes
 * @progress_user_data: data to pass to @progress_callback
 * @error: the #GError to store any failure, or %NULL
 *
 * Recover from broken dependencies of installed packages or incomplete
 * installations.
 *
 * Warning: this function is synchronous, and may block. Do not use it in GUI
 * applications.
 *
 * Return value: (transfer full): a #PkResults object, or %NULL for error
 *
 * Since: 0.7.2
 **/
PkResults *
pk_task_repair_system_sync (PkTask *task, GCancellable *cancellable,
                            PkProgressCallback progress_callback, gpointer progress_user_data,
                            GError **error)
{
	PkTaskHelper helper;
	PkResults *results;

	g_return_val_if_fail (PK_IS_TASK (task), NULL);
	g_return_val_if_fail (error == NULL || *error == NULL, NULL);

	/* create temp object */
	memset (&helper, 0, sizeof (PkTaskHelper));
	helper.context = g_main_context_new ();
	helper.loop = g_main_loop_new (helper.context, FALSE);
	helper.error = error;

	g_main_context_push_thread_default (helper.context);

	/* run async method */
	pk_task_repair_system_async (task, cancellable, progress_callback, progress_user_data,
				     (GAsyncReadyCallback) pk_task_generic_finish_sync,
				     &helper);

	g_main_loop_run (helper.loop);

	results = helper.results;

	g_main_context_pop_thread_default (helper.context);

	/* free temp object */
	g_main_loop_unref (helper.loop);
	g_main_context_unref (helper.context);

	return results;
}
