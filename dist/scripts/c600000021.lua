--SPDX-License-Identifier: AGPL-3.0-or-later
--Treeborn Frog (historical implementation, Retro Formats)
--Upstream: https://github.com/ProjectIgnis/CardScripts/blob/383bfbd62cefc0a28e075acfb78b0bb8203b94c7/official/c12538374.lua
--Copyright (C) 2020  Project Ignis contributors. See version history and author credit line for each file.
--Modified by edopro-retro-formats on 2026-09-29: the Standby Phase effect has no once-per-turn limit (SetCountLimit(1) removed), as the period text carries none and the card FAQ lets it be activated again in the same Standby Phase; the effect description is read from the modern card's strings.
--This modified file is licensed, like its upstream, under the GNU Affero General
--Public License, version 3 or (at your option) any later version. The licence
--text is LICENSE-AGPL-3.0-or-later.txt next to this file in dist/scripts/, and
--LICENSES/AGPL-3.0-or-later.txt in the edopro-retro-formats repository.
--
--Period text: "If this card is in your Graveyard during your Standby Phase and you control no Spell
--or Trap Cards, you can Special Summon it. This effect cannot be activated if you
--control a face-up "Treeborn Frog"."
--
--See data/custom-cards/c600000021.json for what this script does not reproduce.
--黄泉ガエル
--Treeborn Frog
local s,id=GetID()
function s.initial_effect(c)
	--Special Summon
	local e1=Effect.CreateEffect(c)
	e1:SetDescription(aux.Stringid(12538374,0))
	e1:SetType(EFFECT_TYPE_TRIGGER_O+EFFECT_TYPE_FIELD)
	e1:SetCategory(CATEGORY_SPECIAL_SUMMON)
	e1:SetCode(EVENT_PHASE|PHASE_STANDBY)
	e1:SetRange(LOCATION_GRAVE)
	e1:SetCondition(s.condition)
	e1:SetTarget(s.target)
	e1:SetOperation(s.operation)
	c:RegisterEffect(e1)
end
s.listed_names={id}
function s.filter(c)
	return c:IsSpellTrap() or (c:IsCode(id) and c:IsFaceup())
end
function s.condition(e,tp,eg,ep,ev,re,r,rp)
	return tp==Duel.GetTurnPlayer() and not Duel.IsExistingMatchingCard(s.filter,tp,LOCATION_ONFIELD,0,1,nil) 
end
function s.target(e,tp,eg,ep,ev,re,r,rp,chk)
	if chk==0 then return Duel.GetLocationCount(tp,LOCATION_MZONE)>0
		and e:GetHandler():IsCanBeSpecialSummoned(e,0,tp,false,false) end
	Duel.SetOperationInfo(0,CATEGORY_SPECIAL_SUMMON,e:GetHandler(),1,0,0)
end
function s.operation(e,tp,eg,ep,ev,re,r,rp)
	if e:GetHandler():IsRelateToEffect(e) and not Duel.IsExistingMatchingCard(s.filter,tp,LOCATION_ONFIELD,0,1,nil) then
		Duel.SpecialSummon(e:GetHandler(),0,tp,tp,false,false,POS_FACEUP)
	end
end