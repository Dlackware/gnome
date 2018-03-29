/* -*- Mode: C; tab-width: 8; indent-tabs-mode: t; c-basic-offset: 8 -*-
 *
 * Copyright (C) 2009 Richard Hughes <richard@hughsie.com>
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

#if !defined (__PACKAGEKIT_H_INSIDE__) && !defined (PK_COMPILATION)
#error "Only <packagekit.h> can be included directly."
#endif

#ifndef __PK_REPO_SIGNATURE_REQUIRED_H
#define __PK_REPO_SIGNATURE_REQUIRED_H

#include <glib-object.h>

#include <packagekit-glib2/pk-source.h>

G_BEGIN_DECLS

#define PK_TYPE_REPO_SIGNATURE_REQUIRED		(pk_repo_signature_required_get_type ())
#define PK_REPO_SIGNATURE_REQUIRED(o)		(G_TYPE_CHECK_INSTANCE_CAST ((o), PK_TYPE_REPO_SIGNATURE_REQUIRED, PkRepoSignatureRequired))
#define PK_REPO_SIGNATURE_REQUIRED_CLASS(k)	(G_TYPE_CHECK_CLASS_CAST((k), PK_TYPE_REPO_SIGNATURE_REQUIRED, PkRepoSignatureRequiredClass))
#define PK_IS_REPO_SIGNATURE_REQUIRED(o)	(G_TYPE_CHECK_INSTANCE_TYPE ((o), PK_TYPE_REPO_SIGNATURE_REQUIRED))
#define PK_IS_REPO_SIGNATURE_REQUIRED_CLASS(k)	(G_TYPE_CHECK_CLASS_TYPE ((k), PK_TYPE_REPO_SIGNATURE_REQUIRED))
#define PK_REPO_SIGNATURE_REQUIRED_GET_CLASS(o)	(G_TYPE_INSTANCE_GET_CLASS ((o), PK_TYPE_REPO_SIGNATURE_REQUIRED, PkRepoSignatureRequiredClass))

typedef struct _PkRepoSignatureRequiredPrivate	PkRepoSignatureRequiredPrivate;
typedef struct _PkRepoSignatureRequired		PkRepoSignatureRequired;
typedef struct _PkRepoSignatureRequiredClass	PkRepoSignatureRequiredClass;

#ifdef G_DEFINE_AUTOPTR_CLEANUP_FUNC
G_DEFINE_AUTOPTR_CLEANUP_FUNC(PkRepoSignatureRequired, g_object_unref)
#endif

struct _PkRepoSignatureRequired
{
	 PkSource			 parent;
	 PkRepoSignatureRequiredPrivate	*priv;
};

struct _PkRepoSignatureRequiredClass
{
	PkSourceClass	parent_class;
	/* padding for future expansion */
	void (*_pk_reserved1) (void);
	void (*_pk_reserved2) (void);
	void (*_pk_reserved3) (void);
	void (*_pk_reserved4) (void);
	void (*_pk_reserved5) (void);
};

GType			 pk_repo_signature_required_get_type		(void);
PkRepoSignatureRequired	*pk_repo_signature_required_new			(void);

G_END_DECLS

#endif /* __PK_REPO_SIGNATURE_REQUIRED_H */

