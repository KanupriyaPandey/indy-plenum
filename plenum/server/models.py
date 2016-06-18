"""
Some model objects used in Plenum protocol.
"""
from typing import NamedTuple, Set

from plenum.common.types import Commit, Prepare

ThreePhaseVotes = NamedTuple("ThreePhaseVotes", [
    ("digest", str),
    ("voters", Set[str])])


InsChgVotes = NamedTuple("InsChg", [
    ("viewNo", int),
    ("voters", Set[str])])


class TrackedMsgs(dict):

    def newVoteMsg(self, msg):
        raise NotImplementedError

    def getKey(self, msg):
        raise NotImplementedError

    def addMsg(self, msg, voter: str):
        key = self.getKey(msg)
        if key not in self:
            self[key] = self.newVoteMsg(msg)
        self[key].voters.add(voter)

    def hasMsg(self, msg):
        key = self.getKey(msg)
        return key in self

    def hasVote(self, msg, voter: str) -> bool:
        key = self.getKey(msg)
        return key in self and voter in self[key].voters

    def hasEnoughVotes(self, msg, count):
        key = self.getKey(msg)
        return self.hasMsg(msg) and len(self[key].voters) >= count


class Prepares(TrackedMsgs):
    """
    Dictionary of received Prepare requests. Key of dictionary is a 2
    element tuple with elements viewNo, seqNo and value is a 2 element
    tuple containing request digest and set of sender node names(sender
    replica names in case of multiple protocol instances)
    (viewNo, seqNo) -> (digest, {senders})
    """

    def newVoteMsg(self, msg):
        return ThreePhaseVotes(msg.digest, set())

    def getKey(self, prepare):
        return prepare.viewNo, prepare.ppSeqNo

    # noinspection PyMethodMayBeStatic
    def addVote(self, prepare: Prepare, voter: str) -> None:
        """
        Add the specified PREPARE to this replica's list of received
        PREPAREs.

        :param prepare: the PREPARE to add to the list
        :param voter: the name of the node who sent the PREPARE
        """
        super().addMsg(prepare, voter)

    # noinspection PyMethodMayBeStatic
    def hasPrepare(self, prepare: Prepare) -> bool:
        return super().hasMsg(prepare)

    # noinspection PyMethodMayBeStatic
    def hasPrepareFrom(self, prepare: Prepare, voter: str) -> bool:
        return super().hasVote(prepare, voter)

    def hasQuorum(self, prepare: Prepare, f: int) -> bool:
        return self.hasEnoughVotes(prepare, 2 * f)


class Commits(TrackedMsgs):
    """
    Dictionary of received commit requests. Key of dictionary is a 2
    element tuple with elements viewNo, seqNo and value is a 2 element
    tuple containing request digest and set of sender node names(sender
    replica names in case of multiple protocol instances)
    """

    def newVoteMsg(self, msg):
        return ThreePhaseVotes(msg.digest, set())

    def getKey(self, commit):
        return commit.viewNo, commit.ppSeqNo

    # noinspection PyMethodMayBeStatic
    def addVote(self, commit: Commit, voter: str) -> None:
        """
        Add the specified COMMIT to this replica's list of received
        COMMITs.

        :param commit: the COMMIT to add to the list
        :param voter: the name of the replica who sent the COMMIT
        """
        super().addMsg(commit, voter)

    # noinspection PyMethodMayBeStatic
    def hasCommit(self, commit: Commit) -> bool:
        return super().hasMsg(commit)

    # noinspection PyMethodMayBeStatic
    def hasCommitFrom(self, commit: Commit, voter: str) -> bool:
        return super().hasVote(commit, voter)

    def hasQuorum(self, commit: Commit, f: int) -> bool:
        return self.hasEnoughVotes(commit, 2 * f + 1)


class InstanceChanges(TrackedMsgs):
    """
    Stores senders of received instance change requests. Key is the view
    no and and value is the set of senders
    """

    def newVoteMsg(self, msg):
        return InsChgVotes(msg, set())

    def getKey(self, viewNo):
        return viewNo

    # noinspection PyMethodMayBeStatic
    def addVote(self, viewNo: int, voter: str):
        super().addMsg(viewNo, voter)

    # noinspection PyMethodMayBeStatic
    def hasView(self, viewNo: int) -> bool:
        return super().hasMsg(viewNo)

    # noinspection PyMethodMayBeStatic
    def hasInstChngFrom(self, viewNo: int, voter: str) -> bool:
        return super().hasVote(viewNo, voter)

    def hasQuorum(self, viewNo: int, f: int) -> bool:
        return self.hasEnoughVotes(viewNo, 2 * f + 1)