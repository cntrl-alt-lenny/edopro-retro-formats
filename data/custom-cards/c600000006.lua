--Green Baboon, Defender of the Forest (historical implementation, Retro Formats)
--Original script for edopro-retro-formats (MIT). Written from the period card text
--and the engine's Lua API; it is not a copy or an adaptation of any Project Ignis
--CardScripts file, whose licence (AGPL-3.0-or-later) this repository does not carry.
--
--Period text: "When a Beast-Type monster you control is destroyed and sent to the
--Graveyard, you can pay 1000 Life Points to Special Summon this card from your hand or
--the Graveyard."
--
--Implemented: a trigger effect of this card in the hand or Graveyard. Unlike the modern
--card it does not ask for the Beast to have been face-up, and it may be activated when
--the Beast is destroyed in the Damage Step. The 1000 Life Points are a cost. This card
--itself being the destroyed Beast does not count as the trigger.
--See data/custom-cards/c600000006.json for what this script does not reproduce.
local s,id=GetID()
function s.initial_effect(c)
	local e1=Effect.CreateEffect(c)
	e1:SetCategory(CATEGORY_SPECIAL_SUMMON)
	e1:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_TRIGGER_O)
	e1:SetCode(EVENT_TO_GRAVE)
	e1:SetProperty(EFFECT_FLAG_DELAY)
	e1:SetRange(LOCATION_HAND+LOCATION_GRAVE)
	e1:SetCondition(s.condition)
	e1:SetCost(s.cost)
	e1:SetTarget(s.target)
	e1:SetOperation(s.operation)
	c:RegisterEffect(e1)
end
function s.cfilter(c,tp)
	return c:IsPreviousControler(tp) and c:IsPreviousLocation(LOCATION_MZONE) and c:IsPreviousPosition(POS_FACEUP)
		and c:IsReason(REASON_DESTROY) and (c:GetPreviousRaceOnField()&RACE_BEAST)~=0
end
function s.condition(e,tp,eg,ep,ev,re,r,rp)
	return eg:IsExists(s.cfilter,1,e:GetHandler(),tp)
end
function s.cost(e,tp,eg,ep,ev,re,r,rp,chk)
	if chk==0 then return Duel.CheckLPCost(tp,1000) end
	Duel.PayLPCost(tp,1000)
end
function s.target(e,tp,eg,ep,ev,re,r,rp,chk)
	local c=e:GetHandler()
	if chk==0 then
		return Duel.GetLocationCount(tp,LOCATION_MZONE)>0 and c:IsCanBeSpecialSummoned(e,0,tp,false,false)
	end
	Duel.SetOperationInfo(0,CATEGORY_SPECIAL_SUMMON,c,1,0,0)
end
function s.operation(e,tp,eg,ep,ev,re,r,rp)
	local c=e:GetHandler()
	if c:IsRelateToEffect(e) then
		Duel.SpecialSummon(c,0,tp,tp,false,false,POS_FACEUP)
	end
end
