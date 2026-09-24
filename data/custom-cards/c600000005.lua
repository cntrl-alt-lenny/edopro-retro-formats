--Strike Ninja (historical implementation, Retro Formats)
--Original script for edopro-retro-formats (MIT). Written from the period card text
--and the engine's Lua API; it is not a copy or an adaptation of any Project Ignis
--CardScripts file, whose licence (AGPL-3.0-or-later) this repository does not carry.
--
--Period text: "You can remove this card from play until the End Phase of this turn by
--removing 2 DARK monsters in your Graveyard from play. You can use this effect during
--either player's turn. You can only use this effect once per turn."
--
--Implemented: a Quick Effect usable in either player's turn whose use limit belongs to
--the card, not to its name, so each copy on the field may use it once per turn. The
--modern card limits the effect by name across all copies. The 2 DARK monsters are
--banished as a cost; this card is banished and returns during the End Phase.
--See data/custom-cards/c600000005.json for what this script does not reproduce.
local s,id=GetID()
function s.initial_effect(c)
	local e1=Effect.CreateEffect(c)
	e1:SetType(EFFECT_TYPE_QUICK_O)
	e1:SetCode(EVENT_FREE_CHAIN)
	e1:SetRange(LOCATION_MZONE)
	e1:SetCountLimit(1,id)
	e1:SetCost(s.cost)
	e1:SetOperation(s.operation)
	c:RegisterEffect(e1)
end
function s.costfilter(c)
	return c:IsAttribute(ATTRIBUTE_DARK) and c:IsAbleToRemoveAsCost()
end
function s.cost(e,tp,eg,ep,ev,re,r,rp,chk)
	if chk==0 then
		return e:GetHandler():IsAbleToRemove()
			and Duel.IsExistingMatchingCard(s.costfilter,tp,LOCATION_GRAVE,0,2,nil)
	end
	Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_REMOVE)
	local g=Duel.SelectMatchingCard(tp,s.costfilter,tp,LOCATION_GRAVE,0,2,2,nil)
	Duel.Remove(g,POS_FACEUP,REASON_COST)
end
function s.operation(e,tp,eg,ep,ev,re,r,rp)
	local c=e:GetHandler()
	if not c:IsRelateToEffect(e) or not c:IsFaceup() then return end
	if Duel.Remove(c,0,REASON_EFFECT+REASON_TEMPORARY)==0 then return end
	local e1=Effect.CreateEffect(c)
	e1:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
	e1:SetCode(EVENT_PHASE+PHASE_END)
	e1:SetReset(RESET_PHASE+PHASE_END)
	e1:SetCountLimit(1)
	e1:SetLabelObject(c)
	e1:SetOperation(s.retop)
	Duel.RegisterEffect(e1,tp)
end
function s.retop(e,tp,eg,ep,ev,re,r,rp)
	Duel.ReturnToField(e:GetLabelObject())
end
