--SPDX-License-Identifier: AGPL-3.0-or-later
--Elemental HERO Chaos Neos (historical implementation, Retro Formats)
--Upstream: https://github.com/ProjectIgnis/CardScripts/blob/383bfbd62cefc0a28e075acfb78b0bb8203b94c7/official/c17032740.lua
--Copyright (C) 2020  Project Ignis contributors. See version history and author credit line for each file.
--Modified by edopro-retro-formats on 2026-09-29: the coin effect has no Main Phase 1 condition (Konami's rulebook lets an Ignition Effect that names no phase be used in either Main Phase); the effect description is read from the modern card's strings.
--This modified file is licensed, like its upstream, under the GNU Affero General
--Public License, version 3 or (at your option) any later version. The licence
--text is LICENSE-AGPL-3.0-or-later.txt next to this file in dist/scripts/, and
--LICENSES/AGPL-3.0-or-later.txt in the edopro-retro-formats repository.
--
--Period text: ""Elemental Hero Neos" + "Neo-Spacian Dark Panther" + "Neo-Spacian Glow Moss"This card
--can only be Special Summoned from your Fusion Deck by returning the above cards you
--control to the Deck. (You do not use "Polymerization".) During the End Phase, return
--this card to the Fusion Deck then Set all face-up monsters currently on the field.
--Once per turn, you can toss a coin 3 times and apply the appropriate effect: ● 3
--Heads: Destroy all monsters your opponent controls. ● 2 Heads: This turn, the effects
--of all face-up monsters your opponent controls are negated. ● 1 Head: Return all
--monsters you control to their owner's hand."
--
--See data/custom-cards/c600000020.json for what this script does not reproduce.
--E・HERO カオス・ネオス
--Elemental HERO Chaos Neos
local s,id=GetID()
function s.initial_effect(c)
	c:EnableReviveLimit()
	--Fusion Summon Procedure
	Fusion.AddProcMix(c,true,true,CARD_NEOS,43237273,17732278)
	Fusion.AddContactProc(c,s.contactfil,s.contactop,s.splimit)
	aux.EnableNeosReturn(c,CATEGORY_POSITION+CATEGORY_SET,s.retinfo,s.retop)
	--Toss a coin 3 times and apply the appropriate effect
	local e1=Effect.CreateEffect(c)
	e1:SetDescription(aux.Stringid(17032740,1))
	e1:SetCategory(CATEGORY_COIN+CATEGORY_DESTROY+CATEGORY_TOHAND)
	e1:SetType(EFFECT_TYPE_IGNITION)
	e1:SetRange(LOCATION_MZONE)
	e1:SetCountLimit(1)
	e1:SetTarget(s.cointg)
	e1:SetOperation(s.coinop)
	c:RegisterEffect(e1)
end
s.listed_names={CARD_NEOS}
s.material_setcode={SET_HERO,SET_ELEMENTAL_HERO,SET_NEOS,SET_NEO_SPACIAN}
s.toss_coin=true
function s.contactfil(tp)
	return Duel.GetMatchingGroup(Card.IsAbleToDeckOrExtraAsCost,tp,LOCATION_ONFIELD,0,nil)
end
function s.contactop(g,tp)
	Duel.ConfirmCards(1-tp,g)
	Duel.SendtoDeck(g,nil,SEQ_DECKSHUFFLE,REASON_COST|REASON_MATERIAL)
end
function s.splimit(e,se,sp,st)
	return not e:GetHandler():IsLocation(LOCATION_EXTRA)
end
function s.retinfo(e,tp,eg,ep,ev,re,r,rp)
	Duel.SetOperationInfo(0,CATEGORY_POSITION,nil,1,PLAYER_ALL,POS_FACEDOWN_DEFENSE)
end
function s.retop(e,tp,eg,ep,ev,re,r,rp)
	local g=Duel.GetMatchingGroup(Card.IsFaceup,tp,LOCATION_MZONE,LOCATION_MZONE,nil)
	Duel.ChangePosition(g,POS_FACEDOWN_DEFENSE)
end
function s.cointg(e,tp,eg,ep,ev,re,r,rp,chk)
	if chk==0 then return true end
	Duel.SetOperationInfo(0,CATEGORY_COIN,nil,0,tp,3)
end
function s.coinop(e,tp,eg,ep,ev,re,r,rp)
	local total_heads=Duel.CountHeads(Duel.TossCoin(tp,3))
	if total_heads==3 then
		local g=Duel.GetFieldGroup(tp,0,LOCATION_MZONE)
		Duel.Destroy(g,REASON_EFFECT)
	elseif total_heads==2 then
		local g=Duel.GetMatchingGroup(Card.IsFaceup,tp,0,LOCATION_MZONE,nil)
		local c=e:GetHandler()
		for tc in g:Iter() do
			local e1=Effect.CreateEffect(c)
			e1:SetType(EFFECT_TYPE_SINGLE)
			e1:SetCode(EFFECT_DISABLE)
			e1:SetReset(RESETS_STANDARD_PHASE_END)
			tc:RegisterEffect(e1)
			local e2=Effect.CreateEffect(c)
			e2:SetType(EFFECT_TYPE_SINGLE)
			e2:SetCode(EFFECT_DISABLE_EFFECT)
			e2:SetReset(RESETS_STANDARD_PHASE_END)
			tc:RegisterEffect(e2)
		end
	elseif total_heads==1 then
		local g=Duel.GetMatchingGroup(Card.IsAbleToHand,tp,LOCATION_MZONE,0,nil)
		Duel.SendtoHand(g,nil,REASON_EFFECT)
	end
end