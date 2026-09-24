--Rise of the Snake Deity (historical implementation, Retro Formats)
--Original script for edopro-retro-formats (MIT). Written from the period card text
--and the engine's Lua API; it is not a copy or an adaptation of any Project Ignis
--CardScripts file, whose licence (AGPL-3.0-or-later) this repository does not carry.
--
--Period text: "Activate only when a face-up "Vennominon the King of Poisonous Snakes"
--you control is destroyed. Special Summon 1 "Vennominaga the Deity of Poisonous Snakes"
--from your hand or Deck."
--
--Vennominaga has a Special Summon condition of its own in the engine (this card was not
--accepted by it), so the Special Summon ignores summoning conditions.
--Implemented: a Normal Trap activated when a face-up "Vennominon the King of Poisonous
--Snakes" you control is destroyed by any cause. Unlike the modern card ("except by
--battle") that includes battle, so it may be activated in the Damage Step.
--See data/custom-cards/c600000007.json for what this script does not reproduce.
local s,id=GetID()
local CARD_VENNOMINON=72677437
local CARD_VENNOMINAGA=8062132
function s.initial_effect(c)
	local e1=Effect.CreateEffect(c)
	e1:SetCategory(CATEGORY_SPECIAL_SUMMON)
	e1:SetType(EFFECT_TYPE_ACTIVATE)
	e1:SetCode(EVENT_DESTROYED)
	e1:SetCondition(s.condition)
	e1:SetTarget(s.target)
	e1:SetOperation(s.operation)
	c:RegisterEffect(e1)
end
function s.cfilter(c,tp)
	return c:IsPreviousControler(tp) and c:IsPreviousPosition(POS_FACEUP)
		and c:IsPreviousLocation(LOCATION_MZONE) and c:IsCode(CARD_VENNOMINON) and not c:IsReason(REASON_BATTLE)
end
function s.condition(e,tp,eg,ep,ev,re,r,rp)
	return eg:IsExists(s.cfilter,1,nil,tp)
end
function s.spfilter(c,e,tp)
	return c:IsCode(CARD_VENNOMINAGA) and c:IsCanBeSpecialSummoned(e,0,tp,true,false)
end
function s.target(e,tp,eg,ep,ev,re,r,rp,chk)
	if chk==0 then
		return Duel.GetLocationCount(tp,LOCATION_MZONE)>0
			and Duel.IsExistingMatchingCard(s.spfilter,tp,LOCATION_HAND+LOCATION_DECK,0,1,nil,e,tp)
	end
	Duel.SetOperationInfo(0,CATEGORY_SPECIAL_SUMMON,nil,1,tp,LOCATION_HAND+LOCATION_DECK)
end
function s.operation(e,tp,eg,ep,ev,re,r,rp)
	if Duel.GetLocationCount(tp,LOCATION_MZONE)<=0 then return end
	Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_SPSUMMON)
	local g=Duel.SelectMatchingCard(tp,s.spfilter,tp,LOCATION_HAND+LOCATION_DECK,0,1,1,nil,e,tp)
	if #g>0 then
		Duel.SpecialSummon(g,0,tp,tp,true,false,POS_FACEUP)
	end
end
