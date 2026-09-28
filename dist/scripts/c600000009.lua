--SPDX-License-Identifier: AGPL-3.0-or-later
--Soul Rope (historical implementation, Retro Formats)
--Upstream: https://github.com/ProjectIgnis/CardScripts/blob/383bfbd62cefc0a28e075acfb78b0bb8203b94c7/official/c37383714.lua
--Copyright (C) 2020  Project Ignis contributors. See version history and author credit line for each file.
--Modified by edopro-retro-formats on 2026-09-27: no "by a card effect" requirement (REASON_EFFECT), and activation allowed in the Damage Step (EFFECT_FLAG_DAMAGE_STEP), as the period text has neither restriction.
--This modified file is licensed, like its upstream, under the GNU Affero General
--Public License, version 3 or (at your option) any later version. The licence
--text is LICENSE-AGPL-3.0-or-later.txt next to this file in dist/scripts/, and
--LICENSES/AGPL-3.0-or-later.txt in the edopro-retro-formats repository.
--
--Period text: "Activate only by paying 1000 Life Points when a monster you control is
--destroyed and sent to the Graveyard, Special Summon 1 Level 4 monster from your Deck."
--
--See data/custom-cards/c600000009.json for what this script does not reproduce.
--魂の綱
--Soul Rope
local s,id=GetID()
function s.initial_effect(c)
	--Activate
	local e1=Effect.CreateEffect(c)
	e1:SetCategory(CATEGORY_SPECIAL_SUMMON)
	e1:SetType(EFFECT_TYPE_ACTIVATE)
	e1:SetCode(EVENT_TO_GRAVE)
	e1:SetProperty(EFFECT_FLAG_DAMAGE_STEP)
	e1:SetCondition(s.condition)
	e1:SetCost(Cost.PayLP(1000))
	e1:SetTarget(s.target)
	e1:SetOperation(s.activate)
	c:RegisterEffect(e1)
end
function s.cfilter(c,tp)
	return c:IsReason(REASON_DESTROY) and c:IsMonster()
		and c:IsPreviousControler(tp) and c:IsPreviousLocation(LOCATION_MZONE)
end
function s.condition(e,tp,eg,ep,ev,re,r,rp)
	return eg:IsExists(s.cfilter,1,nil,tp)
end
function s.spfilter(c,e,tp)
	return c:GetLevel()==4 and c:IsCanBeSpecialSummoned(e,0,tp,false,false)
end
function s.target(e,tp,eg,ep,ev,re,r,rp,chk)
	if chk==0 then return Duel.GetLocationCount(tp,LOCATION_MZONE)>0
		and Duel.IsExistingMatchingCard(s.spfilter,tp,LOCATION_DECK,0,1,nil,e,tp) end
	Duel.SetOperationInfo(0,CATEGORY_SPECIAL_SUMMON,nil,1,tp,LOCATION_DECK)
end
function s.activate(e,tp,eg,ep,ev,re,r,rp)
	if Duel.GetLocationCount(tp,LOCATION_MZONE)<=0 then return end
	Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_SPSUMMON)
	local g=Duel.SelectMatchingCard(tp,s.spfilter,tp,LOCATION_DECK,0,1,1,nil,e,tp)
	if #g>0 then
		Duel.SpecialSummon(g,0,tp,tp,false,false,POS_FACEUP)
	end
end