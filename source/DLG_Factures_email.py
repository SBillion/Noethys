#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import os

import GestionDB

import CTRL_Bandeau
import CTRL_Liste_factures
import CTRL_Factures_options
import UTILS_Facturation
import UTILS_Envoi_email


class Dialog(wx.Dialog):
    def __init__(self, parent, filtres=[]):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.THICK_FRAME)
        self.parent = parent
        
        # Bandeau
        intro = u"Cochez les factures � envoyer par Email puis cliquez sur le bouton 'Transf�rer vers l'�diteur d'Emails'."
        titre = u"Envoi de factures par Email"
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Emails_piece.png")
        
        # Factures
        self.box_factures_staticbox = wx.StaticBox(self, -1, u"Liste des factures")
        self.ctrl_liste_factures = CTRL_Liste_factures.CTRL(self, filtres=filtres)
        
        # Options
        self.box_options_staticbox = wx.StaticBox(self, -1, u"Options des factures")
        self.ctrl_options = CTRL_Factures_options.CTRL(self)
        
        # Boutons
        self.bouton_aide = wx.BitmapButton(self, -1, wx.Bitmap(u"Images/BoutonsImages/Aide_L72.png", wx.BITMAP_TYPE_ANY))
        self.bouton_ok = wx.BitmapButton(self, -1, wx.Bitmap(u"Images/BoutonsImages/Transferer_editeur_emails.png", wx.BITMAP_TYPE_ANY))
        self.bouton_annuler = wx.BitmapButton(self, -1, wx.Bitmap(u"Images/BoutonsImages/Fermer_L72.png", wx.BITMAP_TYPE_ANY))

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_CLOSE, self.OnBoutonAnnuler)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        
        # Init Contr�les
        self.ctrl_liste_factures.MAJ() 
                

    def __set_properties(self):
        self.bouton_aide.SetToolTipString(u"Cliquez ici pour obtenir de l'aide")
        self.bouton_ok.SetToolTipString(u"Cliquez ici pour transf�rer les factures vers l'�diteur d'Emails")
        self.bouton_annuler.SetToolTipString(u"Cliquez ici pour annuler")
        self.SetMinSize((850, 700))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
                
        # Factures
        box_factures = wx.StaticBoxSizer(self.box_factures_staticbox, wx.VERTICAL)
        box_factures.Add(self.ctrl_liste_factures, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(box_factures, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        # Options
        box_options = wx.StaticBoxSizer(self.box_options_staticbox, wx.VERTICAL)
        box_options.Add(self.ctrl_options, 0, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(box_options, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnBoutonAide(self, event): 
        import UTILS_Aide
        UTILS_Aide.Aide("TransmettreparEmail")

    def OnBoutonAnnuler(self, event): 
        self.ctrl_options.MemoriserParametres() 
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event): 
        """ Aper�u PDF des factures """
        # Validation des donn�es saisies
        tracks = self.ctrl_liste_factures.GetTracksCoches() 
        if len(tracks) == 0 : 
            dlg = wx.MessageDialog(self, u"Vous n'avez s�lectionn� aucune facture � envoyer par Email !", u"Erreur", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # Cr�ation des factures s�lectionn�es
        listeIDfacture = []
        for track in tracks :
            listeIDfacture.append(track.IDfacture) 
        facturation = UTILS_Facturation.Facturation()
        dictOptions=self.ctrl_options.GetOptions()
        resultat = facturation.Impression(listeFactures=listeIDfacture, nomDoc=None, afficherDoc=False, dictOptions=dictOptions, repertoire=dictOptions["repertoire_copie"], repertoireTemp=True)
        if resultat == False : 
            return
        dictChampsFusion, dictPieces = resultat
        
        def SupprimerFichiersTemp():
            for IDfacture, fichier in dictPieces.iteritems() :
                os.remove(fichier)  

        # R�cup�ration de toutes les adresses Emails
        DB = GestionDB.DB()
        req = """SELECT IDindividu, mail, travail_mail
        FROM individus;"""
        DB.ExecuterReq(req)
        listeAdressesIndividus = DB.ResultatReq()
        DB.Close() 
        dictAdressesIndividus = {}
        for IDindividu, mail, travail_mail in listeAdressesIndividus :
            dictAdressesIndividus[IDindividu] = {"perso" : mail, "travail" : travail_mail}
                
        # R�cup�ration des donn�es adresse + champs + pi�ces
        listeDonnees = []
        listeAnomalies = []
        listeEnvoiNonDemande = []
        for track in tracks :
            adresse = None
            
            # Si Famille inscrite � l'envoi par Email :
            if track.email == True : 
                IDindividu, categorie, adresse = track.email_factures.split(";")
                if IDindividu != "" :
                    if dictAdressesIndividus.has_key(int(IDindividu)) :
                        adresse = dictAdressesIndividus[int(IDindividu)][categorie]
            
            # Si famille non inscrite � l'envoi par Email
            else :
                adresse = UTILS_Envoi_email.GetAdresseFamille(track.IDfamille, choixMultiple=False, muet=True, nomTitulaires=track.nomsTitulaires)
            
            # M�morisation des donn�es
            if adresse not in (None, "", []) : 
                if dictPieces.has_key(track.IDfacture) :
                    fichier = dictPieces[track.IDfacture]
                    champs = dictChampsFusion[track.IDfacture]
                    listeDonnees.append({"adresse" : adresse, "pieces" : [fichier,], "champs" : champs})
                    if track.email == False :
                        listeEnvoiNonDemande.append(track.nomsTitulaires) 
            else :
                listeAnomalies.append(track.nomsTitulaires)

        
        # Annonce les anomalies trouv�es
        if len(listeAnomalies) > 0 :
            texte = u"%d des familles s�lectionn�es n'ont pas d'adresse Email.\n\n" % len(listeAnomalies)
            texte += u"Souhaitez-vous quand m�me continuer avec les %d autres familles ?" % len(listeDonnees)
            dlg = wx.MessageDialog(self, texte, u"Avertissement", wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                SupprimerFichiersTemp()
                return        

        # Annonce les envois non demand�s
        if len(listeEnvoiNonDemande) > 0 :
            texte = u"%d des familles s�lectionn�es n'ont pas demand� d'envoi par Email de leur facture :\n\n" % len(listeEnvoiNonDemande)
            texte += u"Souhaitez-vous quand m�me leur envoyer une facture ?"
            dlg = wx.MessageDialog(self, texte, u"Avertissement", wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                SupprimerFichiersTemp()
                return        
        
        # Derni�re v�rification avant transfert
        if len(listeDonnees) == 0 : 
            dlg = wx.MessageDialog(self, u"Il ne reste finalement aucune facture � envoyer par Email !", u"Erreur", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            SupprimerFichiersTemp()
            return

        # Transfert des donn�es vers DLG Mailer
        import DLG_Mailer
        dlg = DLG_Mailer.Dialog(self, categorie="facture")
        dlg.SetDonnees(listeDonnees, modificationAutorisee=False)
        dlg.ChargerModeleDefaut()
        dlg.ShowModal() 
        dlg.Destroy()

        # Suppression des PDF temporaires
        SupprimerFichiersTemp()




if __name__ == u"__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dlg = Dialog(None)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()